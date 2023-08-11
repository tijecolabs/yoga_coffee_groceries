import os

old_head = os.environ.get("OLD_HEAD")
new_head = os.environ.get("NEW_HEAD")

changed_lines = []

with open("cities.csv", "r") as file:
    lines = file.readlines()

    for idx, line in enumerate(lines):
        if idx == 0:
            continue
        if old_head in line or new_head in line:
            changed_lines.append(line)

# Extract added lines
added_lines = [line for line in changed_lines if new_head in line]

# Write added lines to the added_lines.txt file
with open("added_lines.txt", "w") as file:
    file.writelines(added_lines)
