from domain_models import Side

side = Side.Sell

if type(side) is Side:
    print("ok")
    side = side.value

print(side)