from nba_api.stats.static import players
from nba_api.stats.endpoints import shotchartdetail
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# 畫球場的輔助函式
def draw_court(ax=None, color="black", lw=1):
    if ax is None:
        ax = plt.gca()

    # ---- NBA ShotChart Coordinate Realistic Values ----
    court_width = 500     # roughly -250 to 250
    half_court_len = 470  # Y from 0 to 470

    # Key dimensions tuned to real NBA shotchart
    paint_width = 160      # 80 left + 80 right
    paint_height = 190
    FT_RADIUS = 30      # 罰球圈半徑（真實比例）
    FT_CENTER_Y = 190      # 罰球圈中心位置
    corner_three_height = 90
    three_radius = 238     # 三分弧頂約 y=238–245

    # Basket
    hoop = patches.Circle((0, 0), radius=7.5, color=color, fill=False, lw=lw)

    # Paint zone
    paint = patches.Rectangle(
        (-paint_width/2, 0),
        paint_width,
        paint_height,
        fill=False,
        lw=lw,
        color=color
    )

    # Free throw circle
    ft_circle = patches.Circle(
        (0, FT_CENTER_Y),
        FT_RADIUS,
        fill=False,
        lw=lw,
        color=color
    )

    # Corner three straight lines
    corner_left = patches.Rectangle((-220, 0), 0, corner_three_height, lw=lw, color=color, fill=False)
    corner_right = patches.Rectangle((220, 0), 0, corner_three_height, lw=lw, color=color, fill=False)

    # Three-point arc
    three_arc = patches.Arc(
        (0, 0),
        2 * three_radius,
        2 * three_radius,
        theta1=22,
        theta2=158,
        lw=lw,
        color=color
    )

    # Outer boundary
    outer = patches.Rectangle(
        (-court_width/2, 0),
        court_width,
        half_court_len,
        lw=lw,
        fill=False,
        color=color
    )

    for e in [hoop, paint, ft_circle, corner_left, corner_right, three_arc, outer]:
        ax.add_patch(e)

    ax.set_xlim(-250, 250)
    ax.set_ylim(0, 470)

    return ax

# 1. 找到 Stephen Curry 的 player ID
player_dict = players.get_players()
curry = [p for p in player_dict if p['full_name'] == "Stephen Curry"][0]
curry_id = curry['id']

# 2. 抓 2024-25 球季 Curry 的全部出手（FGA）
shotchart = shotchartdetail.ShotChartDetail(
    player_id=curry_id,
    team_id=1610612744,           # GSW 勇士
    season_type_all_star='Regular Season',
    season_nullable='2024-25',
    context_measure_simple='FGA'  # 所有出手，不只進球
)

# 3. 轉成 DataFrame
df = shotchart.get_data_frames()[0]

print(df.head())
print("筆數：", len(df))
print("EVENT_TYPE 統計：")
print(df['EVENT_TYPE'].value_counts())

# 4. 用 EVENT_TYPE 區分「有進 / 沒進」
made_shots = df[df['EVENT_TYPE'] == 'Made Shot']
missed_shots = df[df['EVENT_TYPE'] == 'Missed Shot']
# -----------------------------
# 4-1. 基本投籃分區命中率
# -----------------------------
df['IS_MADE'] = df['EVENT_TYPE'] == 'Made Shot'

def calc_fg(data):
    att = len(data)
    made = data['IS_MADE'].sum()
    fg_pct = made / att if att > 0 else 0
    return att, made, fg_pct

rows = []

# Overall
att, made, pct = calc_fg(df)
rows.append(["Overall", att, made, pct])

# 3PT vs 2PT
is_three = df['SHOT_TYPE'].str.contains("3PT")
att, made, pct = calc_fg(df[is_three])
rows.append(["3PT", att, made, pct])

att, made, pct = calc_fg(df[~is_three])
rows.append(["2PT", att, made, pct])

# Restricted Area（禁區） / 非禁區油漆區 / 中距離
att, made, pct = calc_fg(df[df['SHOT_ZONE_BASIC'] == "Restricted Area"])
rows.append(["Restricted Area", att, made, pct])

att, made, pct = calc_fg(df[df['SHOT_ZONE_BASIC'] == "In The Paint (Non-RA)"])
rows.append(["In The Paint (Non-RA)", att, made, pct])

att, made, pct = calc_fg(df[df['SHOT_ZONE_BASIC'] == "Mid-Range"])
rows.append(["Mid-Range", att, made, pct])

summary_df = pd.DataFrame(rows, columns=["Zone", "Att", "Made", "FG%"])
summary_df["FG%"] = (summary_df["FG%"] * 100).round(1)

print("\n===== Curry 2024-25 Shooting Summary =====")
print(summary_df)

# 存成 csv，之後可以放報告 / Excel 再畫圖
summary_df.to_csv("curry_2024_25_shooting_summary.csv", index=False)

print("命中數：", len(made_shots), "未進數：", len(missed_shots))

# 5. 畫 Shot Chart（含球場線）
fig, ax = plt.subplots(figsize=(6, 6))

# 先畫球場
draw_court(ax, color="black", lw=1)

# Missed：紅色叉叉
ax.scatter(
    missed_shots['LOC_X'],
    missed_shots['LOC_Y'],
    s=30,
    alpha=0.7,
    c='red',
    marker='x',
    label='Missed',
    zorder=1
)

# Made：綠色實心圓點
ax.scatter(
    made_shots['LOC_X'],
    made_shots['LOC_Y'],
    s=28,
    alpha=0.8,
    c='green',
    edgecolors='black',
    linewidths=0.3,
    marker='o',
    label='Made',
    zorder=2
)

ax.set_title("Stephen Curry 2024-25 Shot Chart")
ax.set_xlabel("LOC_X")
ax.set_ylabel("LOC_Y")
ax.legend()

ax.set_aspect('equal', adjustable='box')

plt.savefig("curry_shotchart_court.png", dpi=300, bbox_inches='tight')
plt.show()