import numpy as np
import json
from string import Template

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


data = {int(x):int(y) for x, y in zip((x-1).tolist(), y.tolist())}

data['maxlvl'] = int(x[-1] + 1)
def make(pricelvldata, elmid, varname, lvldata):
    def strdata(data):
        return json.dumps(data).replace(' ', '')
    t = Template("""new ShopItem("$elmid", $pricedata).setevents(e => {$varname = $lvldata[e.detail.oldlevel]; updatestats()}, e => {$varname = $lvldata2[e.detail.oldlevel]; updatestats()});""")
    return t.substitute(elmid=elmid, pricedata=strdata(pricelvldata), varname=varname, lvldata=strdata(lvldata), lvldata2=strdata([0]+lvldata))

print(data)

print(make(data, input("elemid: "), input("varname: "), list(x.tolist())[:-1]))
