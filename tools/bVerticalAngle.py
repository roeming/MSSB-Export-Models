import matplotlib.pyplot as plt
import math

vertical_angles = [[[[-50, 50], [50, 100], [100, 300], [300, 400], [400, 500]], [[50, 150], [150, 200], [200, 250], [250, 300], [300, 350]], [[50, 150], [150, 200], [150, 200], [200, 300], [300, 350]], [[50, 150], [150, 200], [200, 250], [250, 300], [300, 350]], [[-50, 50], [50, 100], [100, 300], [300, 400], [400, 500]]], [[[400, 450], [450, 500], [500, 550], [550, 600], [550, 600]], [[50, 100], [100, 150], [300, 400], [350, 450], [400, 500]], [[100, 200], [350, 400], [450, 500], [500, 550], [530, 580]], [[50, 100], [100, 150], [300, 400], [350, 450], [400, 500]], [[400, 450], [450, 500], [500, 550], [550, 600], [550, 600]]]];
weights = [[[[[0, 10, 20, 30, 40], [20, 20, 20, 20, 20], [10, 25, 30, 25, 10], [20, 20, 20, 20, 20], [40, 30, 20, 10, 0]], [[0, 10, 20, 30, 40], [20, 20, 20, 20, 20], [10, 25, 30, 25, 10], [20, 20, 20, 20, 20], [40, 30, 20, 10, 0]]], [[[10, 0, 20, 30, 40], [20, 22, 22, 28, 8], [20, 25, 25, 25, 5], [20, 22, 22, 28, 8], [10, 0, 20, 30, 40]], [[10, 0, 20, 30, 40], [20, 22, 22, 28, 8], [20, 25, 25, 25, 5], [20, 22, 22, 28, 8], [10, 0, 20, 30, 40]]]], [[[[0, 10, 20, 30, 40], [5, 5, 15, 40, 35], [5, 5, 20, 40, 35], [5, 5, 15, 40, 35], [40, 30, 20, 10, 0]], [[0, 10, 20, 30, 40], [5, 5, 15, 40, 35], [5, 5, 20, 40, 35], [5, 5, 15, 40, 35], [40, 30, 20, 10, 0]]], [[[5, 0, 10, 40, 45], [5, 21, 12, 29, 33], [5, 23, 15, 27, 30], [5, 21, 12, 29, 33], [5, 0, 10, 40, 45]], [[5, 0, 10, 40, 45], [5, 21, 12, 29, 33], [5, 23, 15, 27, 30], [5, 21, 12, 29, 33], [5, 0, 10, 40, 45]]]], [[[[10, 20, 20, 20, 30], [35, 40, 15, 5, 5], [30, 40, 20, 5, 5], [35, 40, 15, 5, 5], [40, 30, 20, 5, 5]], [[10, 20, 20, 20, 30], [35, 40, 15, 5, 5], [30, 40, 20, 5, 5], [35, 40, 15, 5, 5], [40, 30, 20, 5, 5]]], [[[10, 0, 20, 30, 40], [35, 30, 22, 10, 3], [30, 30, 25, 15, 0], [35, 30, 22, 10, 3], [10, 0, 20, 30, 40]], [[10, 0, 20, 30, 40], [35, 30, 22, 10, 3], [30, 30, 25, 15, 0], [35, 30, 22, 10, 3], [10, 0, 20, 30, 40]]]]];
transparency = "40"
colors = [x + transparency for x in ["#ff0000", "#ffff00", "#00ff00", "#0000ff", "#4B0082"]]

SHORT_ARRAY_ARRAY_807b6af4 = [[0, 0], [500, 550], [500, 550]]
NonCaptainStarSwingBattingVerticalAngleRanges = [[[250, 300], [300, 350], [350, 400], [400, 450], [450, 500]], [[50, 100], [50, 100], [50, 100], [50, 100], [50, 100]], [[120, 160], [160, 200], [160, 200], [160, 200], [120, 160]]]
CaptainStarSwingBattingVerticalAngleRanges = [[[59, 61], [59, 61], [59, 61], [59, 61], [59, 61]], [[-101, -99], [-101, -99], [-101, -99], [-101, -99], [-101, -99]], [[350, 400], [350, 400], [350, 400], [350, 400], [350, 400]], [[450, 500], [450, 500], [450, 500], [450, 500], [450, 500]], [[120, 160], [160, 200], [160, 200], [160, 200], [120, 160]], [[250, 300], [250, 300], [250, 300], [250, 300], [250, 300]], [[64, 80], [64, 80], [64, 80], [64, 80], [64, 80]], [[64, 80], [64, 80], [64, 80], [64, 80], [64, 80]], [[350, 400], [350, 400], [350, 400], [350, 400], [350, 400]], [[200, 250], [200, 250], [200, 250], [200, 250], [200, 250]], [[350, 600], [350, 600], [350, 600], [350, 600], [350, 600]], [[350, 600], [350, 600], [350, 600], [350, 600], [350, 600]]]


def int_to_angle(i):
    return round(i * 360 / 4096, 2)

def angle_to_xy(a) -> tuple[int, int]:
    return math.cos(math.radians(a)), math.sin(math.radians(a))

def get_slice(b, e, c = 100, length = 1):
    x = [0]
    y = [0]
    for i in range(c + 1):
        p = b + ((e - b) * i) / c
        pp = angle_to_xy(p)
        x.append(pp[0] * length)
        y.append(pp[1] * length)
    return x,y

def create_plot(title:str, angles):

    these_weights = [x["Weight"] for x in angles]

    plt.figure(figsize=(12,12), clear=True)
    plt.xlim(-0.2, 1.2)
    plt.ylim(-0.2, 1.2)

    plt.fill([-0.2, -0.2, -0.1, -0.1], [0.0, -0.1, -0.1, 0.0], color="black")
    frame_data = ""
    for i, weight in enumerate(these_weights):
        these_angles = angles[i]["Angles"]
        x, y = get_slice(these_angles[0], these_angles[1], length = 1 + i % 3 * 0.1)
        x_mid, y_mid = (sum(x) / len(x), sum(y) / len(y))
        plt.fill(x, y, color=colors[i])
        plt.text(x_mid, y_mid, f" R{i+1} {weight}%", size = 8)
        l = f"{weight}% for {these_angles[0]}\N{DEGREE SIGN} to {these_angles[1]}\N{DEGREE SIGN}"
        print(l)
        frame_data += l + "\n"
    plt.plot((0, angle_to_xy(0)[0]), (0, angle_to_xy(0)[1]), "black")
    plt.plot((0, angle_to_xy(90)[0]), (0, angle_to_xy(90)[1]), "black")
    plt.title(title)
    plt.legend([frame_data], loc='upper left')
    plt.savefig("VAngles\\" + title + ".png")
    plt.close()


for traj, traj_str in enumerate(["MidTraj","HighTraj", "LowTraj"]):
    for slap_charge, slap_charge_str in enumerate(["Slap", "Charge"]):
        for contact, contact_str in enumerate(["Left Sour", "Left Nice", "Perfect", "Right Nice", "Right Sour"]):
            for easyBatting, easyBatting_str in enumerate(["Regular Batting"]):
                these_weights = weights[traj][slap_charge][easyBatting][contact]
                title = f"{traj_str}, {slap_charge_str}, {contact_str}"
                print(title)

                all_angles = [{"Weight": w, "Angles": [int_to_angle(x) for x in vertical_angles[slap_charge][contact][i]]} for i, w in enumerate(these_weights)]
                create_plot(title, all_angles)
                print()


# star hits
STAR_CHARACTERS = ["Mario", "Luigi", "Wario", "Waluigi", "DK", "Diddy", "Bowser", "Bowser JR", "Yoshi", "Birdo", "Peach", "Daisy"]
for char, char_str in enumerate(STAR_CHARACTERS):
    for contact, contact_str in enumerate(["Left Sour", "Left Nice", "Perfect", "Right Nice", "Right Sour"]):
        title = f"{char_str} Star Hit, {contact_str}"
        print(title)

        these_angles = [int_to_angle(x) for x in CaptainStarSwingBattingVerticalAngleRanges[char][contact]]

        all_angles = [{"Weight": 100, "Angles": these_angles}]
        create_plot(title, all_angles)
        print()

NON_CAPTAIN_STAR_HITS = ["Pop Fly", "Grounder", "Line Drive"]
for char, char_str in enumerate(NON_CAPTAIN_STAR_HITS):
    for contact, contact_str in enumerate(["Left Sour", "Left Nice", "Perfect", "Right Nice", "Right Sour"]):
        title = f"{char_str} Star Hit, {contact_str}"
        print(title)

        these_angles = [int_to_angle(x) for x in NonCaptainStarSwingBattingVerticalAngleRanges[char][contact]]
        all_angles = [{"Weight": 100, "Angles": these_angles}]
        create_plot(title, all_angles)
        print()

# Sour Contact on Charge or Changeup SHORT_ARRAY_ARRAY_807b6af4
title = f"Charge Pitch, Sour Contact"
print(title)

these_angles = [int_to_angle(x) for x in SHORT_ARRAY_ARRAY_807b6af4[1]]
all_angles = [{"Weight": 100, "Angles": these_angles}]
create_plot(title, all_angles)
