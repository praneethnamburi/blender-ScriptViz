import csv
import numpy as np

fname = r"P:\data\20210311 - Coach Todd Baseball pitch\Pitching_01_02_Fill500Frm.csv"

#%%
data = []
data_len = []
with open(fname, newline='') as f:
    reader = csv.reader(f)
    for row in reader:
        data.append(row)
        data_len.append(len(row))

#%%
frame_num_col = 0
time_col = 1
pos_col_start = 2

frame_hdr_row = 0
while True:
    if data_len[frame_hdr_row] > 0:
        if data[frame_hdr_row][frame_num_col] == "Frame":
            break
    frame_hdr_row += 1

marker_name_row = 0
while True:
    if data_len[marker_name_row] > 0:
        if data[marker_name_row][time_col] == "Name":
            break
    marker_name_row += 1

marker_names = np.unique(data[marker_name_row][pos_col_start:])
marker_names_valid = [m.replace(':', '_') for m in marker_names]
marker_name_row_valid = [m.replace(':', '_') for m in data[marker_name_row]]

data_start_row = frame_hdr_row + 1

n_data_rows = len(data)-data_start_row
n_data_cols = len(data[data_start_row])

pos = {mname : np.zeros((n_data_rows, 3)) for mname in marker_names_valid}
assert len(marker_names_valid)*3 + 2 == n_data_cols
for row_count in range(data_start_row, len(data)):
    for col_count in range(pos_col_start, n_data_cols):
        x = data[row_count][col_count]
        if x:
            pos[marker_name_row_valid[col_count]][row_count-data_start_row, (col_count+1)%3] = float(x)

# %%
