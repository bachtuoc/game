import streamlit as st
import streamlit as st
import re
import json
import ast
import pandas as pd

from io import BytesIO
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import time
from datetime import datetime, timedelta
# df=pd.read_csv('gold-data.csv')
# df.to_excel('gold-price.xlsx')

st.title("Đề xuất gamification")

st.subheader("Gồm có các nội dung sau:")
st.write('1. Gold Price forcast: phần này đưa ra các dự báo dài hạn giá vàng theo tháng dự trên AI/ML (xem minh họa ở dưới)')
st.write('2. Tin tức: tổng hợp các tin hot về giá vàng (minh họa ở dưới)')
st.write('3. Game thi đấu trading giữa người chơi và AI bot:')
st.write('- Người chơi trading giá vàng, mục tiêu phải có lợi nhuận lớn hơn AI bot trong một khoảng thời gian nào đó')
st.write('- Nếu chiến thắng, người chơi sẽ được tặng voucher/tiền mặt....')
st.write('- Người chơi có thể mua thêm lượt chơi---> tạo doanh thu từ game')
st.write('- Người chơi có thể lựa chọn chiến đấu với nhiều bot')
st.write('- Xem minh họa chơi thử phía dưới.')
df=pd.read_excel('gold-price.xlsx')

df["Note"] = df["Note"].str.strip().str.title()
# df["Date"] = pd.to_datetime(df["Date"], format="%b-%y")

df2=df[['Date','Price','Note']]
st.set_page_config(layout="wide")
st.subheader("1.Price forecast")

df1=df[df.Note=='Forecast']
st.dataframe(df1[['Date','Price','Khoảng tin cậy']])

fig = px.line(
    df2,
    x="Date",
    y="Price",
    color="Note",
    title="Gold Price: Actual vs Forecast",
    color_discrete_map={
        "Actual": "green",
        "Forecast": "red"
    }
)

fig.update_traces(mode="lines")
st.plotly_chart(fig, use_container_width=True)

st.subheader("News")
st.write('- Precious metals retreat after US payroll surprise')
st.write('- J.P. Morgan sees silver at $81/oz in 2026 after 130% surge')
st.write('- Gold Trading Jumps 240% in Q4 as Volatility Returns')

st.subheader("2.Game")
st.title("🏆 Realtime Gold Trading Battle")

st.write('MỤC TIÊU:')
st.write('- Đặt ít nhất 4 lệnh')
st.write('- Equity > Bot Equity')
st.write('- Profit Target > 0')
st.write('- ...............')
# =====================================================
# INIT SESSION
# =====================================================
if "initialized" not in st.session_state:

    st.session_state.initialized = True
    st.session_state.start_time = datetime.now()
    st.session_state.last_bot_trade = datetime.now()

    st.session_state.current_price = 2500
    st.session_state.price_history = []
    st.session_state.equity_history = []
    st.session_state.orders = []

    st.session_state.player_cash = 10000
    st.session_state.player_gold = 0
    st.session_state.player_positions = []

    st.session_state.bot_cash = 10000
    st.session_state.bot_gold = 0
    st.session_state.bot_positions = []

# =====================================================
# PRICE SIMULATION (Volatility tăng để dễ thấy trade)
# =====================================================
price_change = np.random.normal(0, 20)
st.session_state.current_price += price_change

current_price = st.session_state.current_price
current_time = datetime.now()

st.session_state.price_history.append({
    "time": current_time,
    "price": current_price
})

df_price = pd.DataFrame(st.session_state.price_history)
df_price["MA3"] = df_price["price"].rolling(3).mean()

# =====================================================
# HELPER FUNCTION
# =====================================================
def log_order(who, action, price, pnl=0):
    st.session_state.orders.append({
        "Time": current_time,
        "Who": who,
        "Action": action,
        "Price": round(price,2),
        "PnL": round(pnl,2)
    })

# =====================================================
# UI PRICE
# =====================================================
st.metric("Gold Price", f"${current_price:.2f}")

col1, col2 = st.columns(2)

# =====================================================
# PLAYER ACTION
# =====================================================
st.write('Người chơi bấm vào nút Buy, Sell để đặt lệnh')
with col1:

    if st.button("🟢 Buy"):
        if st.session_state.player_cash >= current_price:
            st.session_state.player_cash -= current_price
            st.session_state.player_gold += 1
            st.session_state.player_positions.append(current_price)
            log_order("Player", "Buy", current_price)

    if st.button("🔴 Sell"):
        if st.session_state.player_gold > 0:
            entry = st.session_state.player_positions.pop(0)
            pnl = current_price - entry

            st.session_state.player_cash += current_price
            st.session_state.player_gold -= 1

            log_order("Player", "Sell", current_price, pnl)

# =====================================================
# BOT STRATEGY (Every 5s demo)
# =====================================================
BOT_INTERVAL = 60  # đổi thành 3600 nếu muốn 1h thật

if (current_time - st.session_state.last_bot_trade).seconds > BOT_INTERVAL:

    ma3 = df_price.iloc[-1]["MA3"]

    if not np.isnan(ma3):

        if current_price > ma3 and st.session_state.bot_cash >= current_price:
            st.session_state.bot_cash -= current_price
            st.session_state.bot_gold += 1
            st.session_state.bot_positions.append(current_price)
            log_order("Bot", "Buy", current_price)

        elif current_price < ma3 and st.session_state.bot_gold > 0:
            entry = st.session_state.bot_positions.pop(0)
            pnl = current_price - entry

            st.session_state.bot_cash += current_price
            st.session_state.bot_gold -= 1

            log_order("Bot", "Sell", current_price, pnl)

    st.session_state.last_bot_trade = current_time

# =====================================================
# PnL CALCULATION
# =====================================================
# Unrealized
player_unrealized = sum(current_price - p for p in st.session_state.player_positions)
bot_unrealized = sum(current_price - p for p in st.session_state.bot_positions)

# Equity
player_equity = (
    st.session_state.player_cash +
    st.session_state.player_gold * current_price
)

bot_equity = (
    st.session_state.bot_cash +
    st.session_state.bot_gold * current_price
)

st.session_state.equity_history.append({
    "time": current_time,
    "Player": player_equity,
    "Bot": bot_equity
})

df_equity = pd.DataFrame(st.session_state.equity_history)

# =====================================================
# DISPLAY STATS
# =====================================================
st.write('Người chơi xem kết quả realtime ở dashboard này:')
colA, colB, colC, colD = st.columns(4)

colA.metric("🔵 Player Equity", f"{player_equity:.2f}")
colB.metric("🔴 Bot Equity", f"{bot_equity:.2f}")
colC.metric("🔵 Player Unrealized", f"{player_unrealized:.2f}")
colD.metric("🔴 Bot Unrealized", f"{bot_unrealized:.2f}")

# =====================================================
# EQUITY CHART
# =====================================================
fig = go.Figure()

fig.add_trace(go.Scatter(
    x=df_equity["time"],
    y=df_equity["Player"],
    name="🔵 Player",
    line=dict(color="blue")
))

fig.add_trace(go.Scatter(
    x=df_equity["time"],
    y=df_equity["Bot"],
    name="🔴 Bot",
    line=dict(color="red")
))

fig.update_layout(title="Realtime Equity Battle")

st.plotly_chart(fig, use_container_width=True)

# =====================================================
# ORDER HISTORY
# =====================================================
st.image("Capture.JPG", width=300)
st.subheader("📜 Order History")

if st.session_state.orders:

    orders_df = pd.DataFrame(st.session_state.orders)

    orders_df["Action"] = orders_df["Action"].apply(
        lambda x: "🟢 Buy" if x=="Buy" else "🔴 Sell"
    )

    # Win rate
    closed = orders_df[
        (orders_df["Action"]=="🔴 Sell") &
        (orders_df["PnL"]!=0)
    ]

    player_trades = closed[closed["Who"]=="Player"]
    bot_trades = closed[closed["Who"]=="Bot"]

    player_wr = (player_trades["PnL"]>0).mean()*100 if not player_trades.empty else 0
    bot_wr = (bot_trades["PnL"]>0).mean()*100 if not bot_trades.empty else 0

    colX, colY = st.columns(2)
    colX.metric("🔵 Player Win Rate", f"{player_wr:.1f}%")
    colY.metric("🔴 Bot Win Rate", f"{bot_wr:.1f}%")

    def highlight(row):
        if row["Who"]=="Player":
            return ['background-color:#e6f2ff']*len(row)
        else:
            return ['background-color:#ffe6e6']*len(row)

    st.dataframe(
        orders_df.sort_values("Time", ascending=False)
        .style.apply(highlight, axis=1),
        use_container_width=True
    )

else:
    st.write("No trades yet")

# =====================================================
# WEEKLY RESULT
# =====================================================
if (current_time - st.session_state.start_time) > timedelta(days=7):

    st.divider()
    if player_equity > bot_equity:
        st.success("🎉 Player Wins This Week!")
    else:
        st.error("🤖 Bot Wins This Week!")

# =====================================================
# AUTO REFRESH
# =====================================================
time.sleep(5)
st.rerun()
