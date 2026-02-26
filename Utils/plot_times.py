import matplotlib.pyplot as plt
import pandas as pd

df = pd.read_csv('decision_logs.csv')
df["datetime"] = pd.to_datetime(df["timestamp"], unit="s")

plt.figure()
plt.ylim(10, 100)

plt.plot(df["datetime"], df["north_g"], label="North")
plt.plot(df["datetime"], df["east_g"], label="East")
plt.plot(df["datetime"], df["south_g"], label="South")
plt.plot(df["datetime"], df["west_g"], label="West")

plt.title("Variation of green times")
plt.xticks(rotation=45)
plt.legend()
plt.tight_layout()
plt.show()
