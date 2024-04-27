import numpy as np

# Your data
x = np.array([1, 2, 3])
y = np.array([20, 270, 360])

def magic():
    # Calculate the coefficients of the linear regression model
    x_mean = np.mean(x)
    y_mean = np.mean(y)

    numerator = np.sum((x - x_mean) * (y - y_mean))
    denominator = np.sum((x - x_mean)**2)

    b1 = numerator / denominator
    b0 = y_mean - (b1 * x_mean)

    # Predict the next number
    next_x = x[-1] + 1   # Assuming the next number is the last number + 1
    next_y = b0 + b1 * next_x
    return next_x, next_y


while True:
    next_x, next_y = magic()
    if next_x > 76:
        break
    print(f"Next number: {next_x}, Predicted value: {next_y}")
    x = np.append(x, next_x)
    y = np.append(y, int(next_y))

x = x-1

data = {x:y for x, y in zip(x.tolist(), y.tolist())}

data['maxlvl'] = x[-1] + 1

import json
from string import Template
make = lambda pricedata, elmid, varname, lvldata: Template("""new ShopItem("$elmid", $pricedata).setevents(e => {$varname = $lvldata[e.detail.oldlevel]; updatestats()}, e => {$varname = $lvldata2[e.detail.oldlevel]; updatestats()});""").substitute(pricedata=json.dumps(pricedata).replace(' ', ''), elmid=elmid, varname=varname, lvldata=json.dumps(lvldata).replace(' ', ''), lvldata2=json.dumps([0]+lvldata).replace(' ', ''))

print(make(data, input("elemid: "), input("varname: "), x.tolist().))
