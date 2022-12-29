from copy import deepcopy
import matplotlib.pyplot as plt


vals = [ 0x32, 0x62, 0x6a, 0x96, 0x1e, 0x5f, 0x6d, 0xaa, 0x28, 0x62, 0x6a, 0xa0, 0x14, 0x5f, 0x6d, 0xb4, 0x3c, 0x63, 0x65, 0x96, 0x28, 0x61, 0x67, 0xaa, 0x37, 0x63, 0x65, 0xa0, 0x23, 0x61, 0x67, 0xb4, 0x32, 0x63, 0x65, 0x8c, 0x28, 0x61, 0x67, 0xa0, 0x2d, 0x63, 0x65, 0x91, 0x23, 0x61, 0x67, 0xa5, 0x50, 0x62, 0x66, 0x78, 0x23, 0x5f, 0x69, 0xa5, 0x50, 0x62, 0x66, 0x6e, 0x23, 0x5f, 0x69, 0xa5, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x28, 0x60, 0x68, 0x96, 0x1e, 0x5d, 0x6b, 0xaa, 0x1e, 0x60, 0x68, 0xaa, 0x14, 0x5d, 0x6b, 0xb4, 0x3c, 0x60, 0x68, 0x8c, 0x23, 0x5d, 0x6b, 0xaa, 0x32, 0x60, 0x68, 0x96, 0x19, 0x5d, 0x6b, 0xb4, 0x3c, 0x63, 0x65, 0x8c, 0x28, 0x61, 0x67, 0xa0, 0x28, 0x63, 0x65, 0xa0, 0x1e, 0x61, 0x67, 0xaa, 0x5a, 0x62, 0x66, 0x6e, 0x4b, 0x5f, 0x69, 0x7d, 0x5a, 0x62, 0x66, 0x6e, 0x4b, 0x5f, 0x69, 0x7d, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00 ]


contacts = [0 for _ in range(8)]
contacts = [deepcopy(contacts) for _ in range(2)]
contacts = [deepcopy(contacts) for _ in range(5)]
contacts = [deepcopy(contacts) for _ in range(2)]

for i, s in enumerate(vals):
    trimmed      = (i // 80) % 2
    slapCharge   = (i // 16) % 5
    easyBatting           = (i // 8)  % 2
    v            = (i // 1)  % 8
    contacts[trimmed][slapCharge][easyBatting][v] = s

line_heights = [0.6,0.2]
transparency = "ff"
colors = [x + transparency for x in ["#ff0000", "#ffff00", "#00ff00", "#0000ff", "#4B0082"]]

for trimmed, trimmed_str in [(0, "Full Length"), (1, "Trimmed")]:
    for slap, slap_str in [(0,"Slap"), (1,"Charge"), (2,"Bunt"), (3,"Star")]:
        for easyBatting, easyBatting_str in [(0, "Regular Batting"), (1, "Easy Batting")]:
            these_contacts = contacts[trimmed][slap][easyBatting]
            rects = [[None,None] for _ in range(4)]
            for i, c in enumerate(these_contacts):
                rects[i%4][i//4] = c
            print(rects)
            plt.figure(figsize=(12,12), clear=True)
            plt.xlim(-.5, 1.5)
            plt.ylim(-0.25, 1.0)

            # fill batter
            # plt.fill([-0.3, -0.3, -0.1, -0.1], [0.2, 0.4, 0.4, 0.2], color="black")

            # plot line
            plt.plot((0.0, 1.0), (line_heights[0], line_heights[0]), "black")
            plt.plot((0.0, 1.0), (line_heights[1], line_heights[1]), "black")
            for i, i_str in [(0, "Worst Scaling"),(1, "Best Scaling")]:
                for ii in range(4):
                    plt.plot((rects[ii][i]/200, rects[ii][i]/200), (line_heights[i] + 0.1, line_heights[i] - 0.1), color = colors[ii])
                    plt.text(rects[ii][i]/200, line_heights[i] + [0.1, -0.1][ii%2], f"{rects[ii][i]}")
                    plt.text(-0.25, line_heights[i], i_str)
            t = f"{easyBatting_str}, {trimmed_str}, {slap_str}"
            plt.title(t)
            l = []
            new_rects = [[0,0], *rects, [200,200]]
            for ii, ii_str in [(0, "Worst"),(1, "Best")]:
                ll = ""
                for i, i_str in enumerate(["LeftSour", "LeftNice", "Perfect", "RightNice", "RightSour"]):
                    ll+=f"{ii_str} {i_str}: {new_rects[i][ii]} to {new_rects[i+1][ii]}"
                    ll+="\n"
                l.append(ll)
            plt.legend(l)
            plt.savefig("ContactGraphs\\" + t + ".png")
            # plt.show()
            plt.close()

