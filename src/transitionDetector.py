import os

import cv2
import matplotlib.pyplot as plt
import numpy as np

from transitions import *


# main function for command line
def detect_transitions(colsti, rowsti, thresh = 40) -> list:
    # detect the lines
    col_lines = _detect_lines(colsti, thresh)
    row_lines = _detect_lines(rowsti, thresh)
    # classify them as transitions
    transitions = _map_lines_to_transitions(col_lines, True)
    transitions += _map_lines_to_transitions(row_lines, False)
    return transitions


# detect high quality lines
# type = true for col, false for row
def _detect_lines(sti, thresh) -> list:
    lines, height = _simple_line_detection(sti, thresh)
    if type(lines) is not list:
        return []
    groups = _first_pass_group(lines)
    lines = _combine_lines(groups, sti)
    finalLines = _weed_false_positives(lines, height)
    # _extrapolate_end_points(lines)
    return lines


# use openCV to find simple lines
def _simple_line_detection(sti, thresh) -> (list,int):
    # I feel like there has to be a better way lol
    cv2.imwrite("temp.png", sti)  # doing this changes it to the correct format
    img = cv2.imread("temp.png")
    height,width,channel = img.shape
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    kernel_size = 5
    blur_gray = cv2.GaussianBlur(gray, (kernel_size, kernel_size), 0)
    low_threshold = 50
    high_threshold = 150
    edges = cv2.Canny(blur_gray, low_threshold, high_threshold)
    rho = 1
    theta = np.pi / 180
    threshold = thresh
    min_line_length = float(0.7*height)
    max_line_gap = 20
    line_image = np.copy(img) * 0
    lines = []
    lines = cv2.HoughLinesP(edges, rho, theta, threshold, np.array([]),
                            min_line_length, max_line_gap)
    try:
        for line in lines:
            for x1, y1, x2, y2 in line:
                cv2.line(line_image, (x1, y1), (x2, y2), (255, 0, 0), 5)

        lines_edges = cv2.addWeighted(img, 0.8, line_image, 1, 0)
        lines = lines.tolist()
        cv2.waitKey(0)
    except TypeError:
        print("no transitions found")
    os.remove("temp.png")
    return lines, height

# group the lines into groups based on how close they are, order by first point
# returns list of groups, (where a group is a list of lines that are close)
def _first_pass_group(lines) -> list:
    xInterceptTol = 20
    slopeTol = 1
    lines.sort(key=lambda x: (math.fabs(x[0][1] - x[0][3])))
    lines_ = np.copy(lines)
    groups = []
    # comparing the lines with with all others
    for line in lines[:]:
        groups_ = [line[0]]
        if float(line[0][2] - line[0][0]) == 0:
            groups.append(groups_)
            continue
        lines_ = np.delete(lines_, 0, 0)  # making sure the checks are not repeated,
        slope = float((line[0][3] - line[0][1]) / (line[0][2] - line[0][0]))
        b = float(line[0][1] - (slope * line[0][0]))  # b from y= mx + b
        xIntercept = float((-1 * b) / slope)
        k = -1
        for cmp in lines_:
            k += 1
            if cmp[0][2] is cmp[0][0]:
                continue
            slope_ = float((cmp[0][3] - cmp[0][1]) / (cmp[0][2] - cmp[0][0]))
            b_ = float(cmp[0][1] - (slope_ * cmp[0][0]))
            xIntercept_ = float((-1 * b_) / slope_)  # compute the intercept
            if abs(slope_ - slope) > slopeTol:
                continue
            if abs(xIntercept_ - xIntercept) > xInterceptTol:
                continue
            groups_.append(cmp[0])  # append if tests pass
        groups.append(groups_)

    return groups


# ALL combine_lines have the same input and output, just different methods of achieving
# # this is just an easy way to toggle between them and see which is better
# # maybe later we will make the combiner a toggle
def _combine_lines(groups,sti) -> list:
    return _linear_regression_(groups)


def _linear_regression_(groups) -> list:
    print("Running linear regression..")
    xlist = []
    ylist = []
    finalLine = []
    beginFrame = []
    for group in groups:
        xlist = []
        ylist = []
        for line in group:
            xlist.append(line[0])
            ylist.append(line[1])
            xlist.append(line[2])
            ylist.append(line[3])
            x = np.array(xlist)
            y = np.array(ylist)
        try:
            xmax = max(xlist)
            xmin = min(xlist)
            coef = np.polyfit(x,y,1)
            poly1d_fn = np.poly1d(coef)
            newL = [xmin, poly1d_fn(xmin), xmax, poly1d_fn(xmax)]
            finalLine.append(newL)
        except:
            continue
        # plt.plot(x, y, 'yo', x, poly1d_fn(x), '--k')
        #plt.show()

    return finalLine

# check each group to see if any of the lines can be combined, return list of lines
def _linear_regression_with_elemination_(groups, sti) -> list:
    print("Running Linear regression with elimination..")
    xList = []
    yList = []

    i = -1
    #   reading the sti
    for row in sti:
        i += 1
        j = 0
        for x in row:
            j += 1
            if x.all() == 0:
                xList.append(i)
                yList.append(j)

    deleted = True

    while deleted:
        x = np.array(xList)
        y = np.array(yList)
        #   setup LR model
        slope, b = np.polyfit(x, y, 1)

        # only for plotting:
        coef = np.polyfit(x, y, 1)
        poly1d_fn = np.poly1d(coef)

        xList, yList, deleted = deleteOutliers(slope=slope, b=b, xlist=xList, yList=yList)

    plt.plot(x, y, 'yo', x, poly1d_fn(x), '--k')
    plt.xlim(-2, 30)
    plt.ylim(-5, 100)
    plt.show()
    return []


def deleteOutliers(slope, b, xlist, yList) -> (list, list, bool):
    distance = []
    for i in range(0, len(xlist)):
        numerator = math.fabs((slope * xlist[i]) + ((-1) * yList[i]) + b)
        denom = math.sqrt((slope * slope) + 1)
        distance.append(float(numerator / denom))

    distance.sort()
    q1 = float(np.quantile(distance, .25))
    q3 = float(np.quantile(distance, .75))
    iqr = float(q3 - q1)
    maxDist = float(q3 + (1.5 * iqr))
    deleted = False
    i = 0
    k = []
    maxRemoveAllowed = 7
    for x in distance:
        if x > maxDist:
            if len(k) > maxRemoveAllowed:
                break
            k.append(i)
            deleted = True
        i += 1
    k.sort(reverse=True)
    for i in k:
        del distance[i]
        del xlist[i]
        del yList[i]
    return xlist, yList, deleted


# feel free to add another method
def _combine_lines_hypothesis(groups) -> list:
    pass


# sort the groups by y2 and combine them
def _combine_lines_thresholded(groups) -> list:
    finallist = []
    for group in groups:
        group = sorted(group, key=lambda x: x[3], reverse=True)
        temp = [group[0][0], group[0][1], group[-1][2], group[-1][3]]
        finallist.append(temp)
    return finallist


# remove any lines that appear to be false positives
def _weed_false_positives(lines, height) -> list:
    threshConst = 0.8*height
    Threshold = threshConst * height
    finalList = []

    try:
        for line in lines:
            dist = float(math.sqrt(math.fabs(((line[2] - line[0]) * (line[2] - line[0])) - ((line[3] - line[1]) * (line[3] - line[1])))))
            isTooClose = True
            i = 0
            for x in lines:
                if x[0]-line[0] < 60:
                    i+=1
                    if i == 2:
                        isTooClose = False
                        break

            if dist > Threshold and isTooClose:
                finalList.append(line)

    except:
        return []

    return finalList


# make the end points be 0 or 1, instead of somewhere in the middle
def _extrapolate_end_points(lines) -> None:
    pass


# simple as it sounds
def _map_lines_to_transitions(lines, col) -> list:
    transitionList = []
    try:
        for line in lines:
            if float(line[0] - line[2]) == 0:
                transitionList.append(Cut(start=line[0]))
                continue
            x = float((line[3] - line[1]) / (line[2] - line[0]))
            b = float(line[1] - (x * line[0]))
            intercept = int((-1 * b) / x)
            theta = math.atan(x)  # slope is tan(theta), so calculate theta and see if its positive or neg
            if theta > 0:
                if col:
                    transitionList.append(ColWipe(start=line[0], end=line[2], scol=0, ecol=1))
                else:
                    transitionList.append(HorWipe(start=line[0], end=line[2], srow=0, erow=1))
            else:
                if theta < 0:
                    if col:
                        transitionList.append(ColWipe(start=line[0], end=line[2], scol=1, ecol=0))
                    else:
                        transitionList.append(HorWipe(start=line[0], end=line[2], srow=1, erow=0))
    # self.listOfTransitions.append(tempTransition)
    except:
        return []
    return transitionList

