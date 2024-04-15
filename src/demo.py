class A:
    id: str

    def __init__(self, id:str):
        self.id = id



array = list()
array.append(A(1))

order_id = [item for item in array if item.id == 15]

if order_id:
    print(True)


