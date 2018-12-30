print ("Starting...")
with open('homologene.data') as f:
    lines = f.readlines()

print ("Parsing..")
allowed_tax_list = [9606, 10090, 10116]
good_lines = [lines[0]]
for line in lines[1:]:
    parts = line.split('\t')
    if int(parts[1].strip()) in allowed_tax_list:
        good_lines.append(line)

with open('homologene_reduced.data', 'w') as fh:
    for i in good_lines:
        fh.write(i)

print ("++Done++")


