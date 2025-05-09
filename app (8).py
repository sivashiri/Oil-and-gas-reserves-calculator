
import streamlit as st
import matplotlib.pyplot as plt

# Set title
st.title("🛢️ Volumetric Oil & Gas Reserves Calculator")

st.write("""
This app estimates Oil Initially in Place (OIIP) and/or Gas Initially in Place (GIIP) using the volumetric method.
""")

# Choose between Oil or Gas
reserve_type = st.radio("Select the type of reserve:", ('Oil', 'Gas'))

# Sliders for inputs
A = st.slider("Area of reservoir (acres)", min_value=10.0, max_value=10000.0, value=500.0, step=10.0)
h = st.slider("Net thickness (feet)", min_value=1.0, max_value=300.0, value=50.0, step=10.0)
phi = st.slider("Porosity (fraction)", min_value=0.05, max_value=0.35, value=0.20, step=0.01)
Sw = st.slider("Water Saturation (fraction)", min_value=0.0, max_value=1.0, value=0.25, step=0.01)

# Formation volume factor sliders
if reserve_type == 'Oil':
    Bo = st.slider("Formation Volume Factor Bo (RB/STB)", min_value=1.0, max_value=2.0, value=1.2, step=0.01)
else:
    Bg = st.slider("Formation Volume Factor Bg (RCF/SCF)", min_value=0.0001, max_value=0.01, value=0.005, step=0.0001)

# Optional Recovery Factor
RF = st.slider("Recovery Factor (optional)", min_value=0.0, max_value=1.0, value=0.0, step=0.01)

factor = 7758 if fluid_type == "oil" else 43560
PV = A * h * factor * phi
HCPV = PV * (1 - Sw)


# Oil or Gas in Place
if reserve_type == 'Oil':
    OIIP = (7758 * A * h * phi * (1 - Sw)) / Bo  # in STB
    st.subheader(f"📊 Oil Initially In Place (OIIP): {OIIP:,.0f} STB")
else:
    GIIP = (43560 * A * h * phi * (1 - Sw)) / Bg  # in SCF
    st.subheader(f"📊 Gas Initially In Place (GIIP): {GIIP:,.0f} SCF")

# Recoverable reserves
if RF > 0:
    if reserve_type == 'Oil':
        recoverable = OIIP * RF
        st.write(f"✅ **Recoverable Oil Reserves:** {recoverable:,.0f} STB")
    else:
        recoverable = GIIP * RF
        st.write(f"✅ **Recoverable Gas Reserves:** {recoverable:,.0f} SCF")
else:
    recoverable = None

# --- Visuals ---

# Bar chart
st.subheader("Bar Chart: Reservoir Volumes")

volumes = ['Pore Volume (PV)', 'Hydrocarbon Pore Volume (HCPV)']
values = [PV, HCPV]

if recoverable:
    volumes.append('Recoverable Reserves')
    values.append(recoverable)

fig, ax = plt.subplots()
ax.bar(volumes, values, color=['skyblue', 'orange', 'green'][:len(values)])
ax.set_ylabel('Volume')
ax.set_title('Comparison of Reservoir Volumes')

st.pyplot(fig)

# Pie chart if Recovery Factor > 0
if RF > 0:
    st.subheader("Pie Chart: Recovery Factor Effect")
    recovered = recoverable
    unrecovered = (OIIP if reserve_type == 'Oil' else GIIP) - recoverable

    fig1, ax1 = plt.subplots()
    ax1.pie([recovered, unrecovered],
            labels=['Recoverable', 'Unrecoverable'],
            autopct='%1.1f%%',
            colors=['lightgreen', 'lightcoral'],
            startangle=90)
    ax1.axis('equal')
    st.pyplot(fig1)

# Footer note
st.write("Note: PV and HCPV are displayed in cubic feet. OIIP is in STB (oil) and GIIP is in SCF (gas).")
