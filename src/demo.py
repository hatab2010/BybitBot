i = None

for item in range(10):
    i = 1

print(i)

while True:
    try:
        if i > 3:
            raise Exception("ex")

        i += 1
    except Exception as ex:
        print("ex")
        break