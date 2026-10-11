"""The promises and their indicators. Every promise is quoted verbatim from a primary source; every indicator is an
official statistical series fetched automatically (no manual entry, no model estimate).

Indicator fields
  id, label, unit, source (key into SOURCES), series (source-specific id), freq (W, M, D)
  better: "lower" | "higher"
  transform: "level" (the observation itself), "trail" (mean or sum over the last `window` periods), "yoy" (12-month %)
  agg: "mean" | "sum" (for trail)
  change: "pct" (percent change) | "diff" (difference in the series' own unit)
  target: optional numeric target stated in or implied by the promise's own words (shown as progress, never weighted)
  max_age: days after which the latest observation counts as stale (then it does not count toward the status)
  band_from / band_note: optional later start of the history used for the noise band, with the reason shown
  tier: "official" (agency release) | "official-foia" (agency records released under FOIA, lagged)
"""

INAUGURAL = "https://www.whitehouse.gov/remarks/2025/01/the-inaugural-address/"

PROMISES = [
    dict(id="prices", title="Bring down costs and prices",
         quote="Next, I will direct all members of my cabinet to marshal the vast powers at their disposal to defeat what was record inflation and rapidly bring down costs and prices.",
         source="Inaugural address, January 20, 2025", url=INAUGURAL,
         kpis=[
             dict(id="cpi_level", label="Consumer prices, all items (CPI-U, seasonally adjusted index)", unit="index", source="bls", series="CUSR0000SA0", freq="M", better="lower", transform="level", change="pct", max_age=75, tier="official"),
             dict(id="cpi_12m", label="Inflation: CPI-U, 12-month change", unit="%", source="bls", series="CUUR0000SA0", freq="M", better="lower", transform="yoy", change="diff", max_age=75, tier="official"),
             dict(id="food_home", label="Food at home (CPI, seasonally adjusted index)", unit="index", source="bls", series="CUSR0000SAF11", freq="M", better="lower", transform="level", change="pct", max_age=75, tier="official"),
             dict(id="eggs", label="Eggs, grade A large, average price per dozen (12-month average)", unit="$", source="bls", series="APU0000708111", freq="M", better="lower", transform="trail", window=12, agg="mean", change="pct", max_age=75, tier="official"),
         ]),
    dict(id="energy_prices", title="Bring energy prices down",
         quote="The inflation crisis was caused by massive overspending and escalating energy prices, and that is why today I will also declare a national energy emergency. […] We will bring prices down, fill our strategic reserves up again right to the top, and export American energy all over the world.",
         source="Inaugural address, January 20, 2025", url=INAUGURAL,
         kpis=[
             dict(id="gasoline_cpi", label="Gasoline (CPI, seasonally adjusted index)", unit="index", source="bls", series="CUSR0000SETB01", freq="M", better="lower", transform="level", change="pct", max_age=75, tier="official"),
             dict(id="gasoline_weekly", label="Regular gasoline, U.S. retail price (52-week average)", unit="$/gal", source="eia", series="pet/hist_xls/EMM_EPMR_PTE_NUS_DPGw.xls", freq="W", better="lower", transform="trail", window=52, agg="mean", change="pct", max_age=21, tier="official"),
             dict(id="electricity_cpi", label="Electricity (CPI, seasonally adjusted index)", unit="index", source="bls", series="CUSR0000SEHF01", freq="M", better="lower", transform="level", change="pct", max_age=75, tier="official"),
         ]),
    dict(id="spr", title="Fill the strategic reserves right to the top",
         quote="We will bring prices down, fill our strategic reserves up again right to the top, and export American energy all over the world.",
         source="Inaugural address, January 20, 2025", url=INAUGURAL,
         note="Target: the Strategic Petroleum Reserve's authorized storage capacity of 714 million barrels (U.S. Department of Energy).",
         kpis=[
             dict(id="spr_stocks", label="Strategic Petroleum Reserve, crude oil stocks", unit="thousand barrels", source="eia", series="pet/hist_xls/WCSSTUS1w.xls", freq="W", better="higher", transform="level", change="pct", target=714000, max_age=21, tier="official"),
         ]),
    dict(id="energy_production", title="Drill, baby, drill: produce and export more energy",
         quote="We will drill, baby, drill. […] We will bring prices down, fill our strategic reserves up again right to the top, and export American energy all over the world.",
         source="Inaugural address, January 20, 2025", url=INAUGURAL,
         kpis=[
             dict(id="crude_prod", label="U.S. crude oil production, weekly estimate (4-week average)", unit="thousand b/d", source="eia", series="pet/hist_xls/WCRFPUS2w.xls", freq="W", better="higher", transform="trail", window=4, agg="mean", change="pct", max_age=21, tier="official"),
             dict(id="gas_prod", label="U.S. dry natural gas production (12-month total)", unit="million cubic feet", source="eia", series="ng/hist_xls/N9070US2m.xls", freq="M", better="higher", transform="trail", window=12, agg="sum", change="pct", max_age=120, tier="official"),
             dict(id="lng_exports", label="U.S. liquefied natural gas exports (12-month total)", unit="million cubic feet", source="eia", series="ng/hist_xls/N9133US2m.xls", freq="M", better="higher", transform="trail", window=12, agg="sum", change="pct", max_age=120, tier="official",
                  band_from="2022-01", band_note="band from 2022 on: U.S. LNG exports grew from almost nothing after 2016, so earlier growth is not typical variation"),
         ]),
    dict(id="manufacturing", title="A manufacturing nation once again",
         quote="America will be a manufacturing nation once again […] We will build automobiles in America again at a rate that nobody could have dreamt possible just a few years ago.",
         source="Inaugural address, January 20, 2025", url=INAUGURAL,
         kpis=[
             dict(id="mfg_jobs", label="Manufacturing employment (seasonally adjusted)", unit="thousands", source="bls", series="CES3000000001", freq="M", better="higher", transform="level", change="pct", max_age=75, tier="official"),
             dict(id="mfg_output", label="Industrial production: manufacturing (index, seasonally adjusted)", unit="index", source="fed", series="GMF", freq="M", better="higher", transform="level", change="pct", max_age=75, tier="official"),
             dict(id="auto_output", label="Industrial production: automobiles and light vehicles (index, seasonally adjusted)", unit="index", source="fed", series="G33611", freq="M", better="higher", transform="level", change="pct", max_age=75, tier="official"),
         ]),
    dict(id="economy", title="The golden age of America",
         quote="[…] and my fellow citizens, the golden age of America begins right now.",
         source="Inaugural address, January 20, 2025", url=INAUGURAL,
         kpis=[
             dict(id="payrolls", label="Nonfarm payroll employment (seasonally adjusted)", unit="thousands", source="bls", series="CES0000000001", freq="M", better="higher", transform="level", change="pct", max_age=75, tier="official"),
             dict(id="unemployment", label="Unemployment rate (seasonally adjusted)", unit="%", source="bls", series="LNS14000000", freq="M", better="lower", transform="level", change="diff", max_age=75, tier="official"),
         ]),
    dict(id="tariff_revenue", title="Tariffs: massive amounts of money pouring into the Treasury",
         quote="For this purpose, we are establishing the External Revenue Service to collect all tariffs, duties, and revenues. It will be massive amounts of money pouring into our Treasury, coming from foreign sources.",
         source="Inaugural address, January 20, 2025", url=INAUGURAL,
         kpis=[
             dict(id="customs_net", label="Customs duties, net receipts after refunds (12-month total)", unit="$ million", source="mts_customs", series="net", freq="M", better="higher", transform="trail", window=12, agg="sum", change="pct", max_age=75, tier="official"),
             dict(id="customs_gross", label="Customs duties, gross receipts (12-month total)", unit="$ million", source="mts_customs", series="gross", freq="M", better="higher", transform="trail", window=12, agg="sum", change="pct", max_age=75, tier="official"),
             dict(id="customs_weekly", label="Customs deposits into the Treasury account (4-week total)", unit="$ million", source="dts_customs", series="customs", freq="W", better="higher", transform="trail", window=4, agg="sum", change="pct", max_age=14, tier="official"),
         ]),
    dict(id="trade_deficit", title="Reduce large and persistent goods trade deficits",
         quote="Regulating Imports With a Reciprocal Tariff To Rectify Trade Practices That Contribute to Large and Persistent Annual United States Goods Trade Deficits",
         source="Executive Order 14257 (title), April 2, 2025",
         url="https://www.federalregister.gov/documents/2025/04/07/2025-06063/regulating-imports-with-a-reciprocal-tariff-to-rectify-trade-practices-that-contribute-to-large-and",
         kpis=[
             dict(id="goods_balance", label="Goods trade balance (seasonally adjusted, monthly; less negative is better)", unit="$ million", source="ft900", series="goods", freq="M", better="higher", transform="level", change="diff", max_age=90, tier="official"),
         ]),
    dict(id="border", title="All illegal entry immediately halted",
         quote="All illegal entry will immediately be halted, and we will begin the process of returning millions and millions of criminal aliens back to the places from which they came.",
         source="Inaugural address, January 20, 2025", url=INAUGURAL,
         note="Target: zero. Baseline: December 2024, the last full month before the inauguration.",
         kpis=[
             dict(id="usbp_sw", label="U.S. Border Patrol apprehensions at the Southwest border (monthly)", unit="persons", source="cbp", series="usbp_sw", freq="M", better="lower", transform="level", change="pct", target=0, max_age=75, tier="official"),
         ]),
    dict(id="removals", title="Returning millions and millions of criminal aliens",
         quote="All illegal entry will immediately be halted, and we will begin the process of returning millions and millions of criminal aliens back to the places from which they came.",
         source="Inaugural address, January 20, 2025", url=INAUGURAL,
         note="DHS's monthly enforcement tables stop at November 2024. Removals are therefore taken from ICE's own case records released under the Freedom of Information Act to the Deportation Data Project (UC Berkeley; CC0), which arrive months late. These records contain one row per removal and run above ICE's published totals (fiscal year 2024: 346,296 rows for 320,424 people, against 271,484 removals in ICE's annual report); the definitions behind the difference are not documented, so the ledger compares the records only with themselves. The detention population is ICE's own statistic.",
         kpis=[
             dict(id="removals_all", label="ICE removals (12-month total, from ICE records released under FOIA)", unit="removals", source="foia_removals", series="all", freq="M", better="higher", transform="trail", window=12, agg="sum", change="pct", max_age=240, tier="official-foia"),
             dict(id="removals_convicted", label="ICE removals of people with a criminal conviction (12-month total)", unit="removals", source="foia_removals", series="convicted", freq="M", better="higher", transform="trail", window=12, agg="sum", change="pct", max_age=240, tier="official-foia"),
             dict(id="ice_detention", label="ICE detention, average daily population (monthly)", unit="persons", source="ice_adp", series="total", freq="M", better="higher", transform="level", change="pct", max_age=60, tier="official"),
         ]),
    dict(id="government", title="End overspending; freeze federal hiring",
         quote="The inflation crisis was caused by massive overspending and escalating energy prices […] I hereby order a freeze on the hiring of Federal civilian employees, to be applied throughout the executive branch.",
         source="Inaugural address, January 20, 2025; Presidential memorandum “Hiring Freeze”, January 20, 2025",
         url="https://www.federalregister.gov/documents/2025/01/28/2025-01905/hiring-freeze",
         kpis=[
             dict(id="outlays", label="Federal outlays (12-month total)", unit="$ million", source="mts_outlays", series="outlays", freq="M", better="lower", transform="trail", window=12, agg="sum", change="pct", max_age=75, tier="official"),
             dict(id="deficit", label="Federal deficit (12-month total)", unit="$ million", source="mts_outlays", series="deficit", freq="M", better="lower", transform="trail", window=12, agg="sum", change="pct", max_age=75, tier="official"),
             dict(id="fed_jobs", label="Federal government employment (seasonally adjusted)", unit="thousands", source="bls", series="CES9091000001", freq="M", better="lower", transform="level", change="pct", max_age=75, tier="official"),
         ]),
    dict(id="drug_prices", title="Most-favored-nation prescription drug prices",
         quote="Delivering Most-Favored-Nation Prescription Drug Pricing to American Patients",
         source="Executive Order 14297 (title), May 12, 2025",
         url="https://www.federalregister.gov/documents/2025/05/15/2025-08876/delivering-most-favored-nation-prescription-drug-pricing-to-american-patients",
         kpis=[
             dict(id="rx_cpi", label="Prescription drugs (CPI, seasonally adjusted index)", unit="index", source="bls", series="CUSR0000SEMF01", freq="M", better="lower", transform="level", change="pct", max_age=75, tier="official"),
         ]),
]

SOURCES = {
    "bls": dict(name="U.S. Bureau of Labor Statistics", url="https://www.bls.gov/data/"),
    "eia": dict(name="U.S. Energy Information Administration", url="https://www.eia.gov/"),
    "fed": dict(name="Federal Reserve Board, G.17 Industrial Production", url="https://www.federalreserve.gov/releases/g17/"),
    "mts_customs": dict(name="U.S. Treasury, Monthly Treasury Statement (Table 4)", url="https://fiscaldata.treasury.gov/datasets/monthly-treasury-statement/"),
    "mts_outlays": dict(name="U.S. Treasury, Monthly Treasury Statement (Table 1)", url="https://fiscaldata.treasury.gov/datasets/monthly-treasury-statement/"),
    "dts_customs": dict(name="U.S. Treasury, Daily Treasury Statement", url="https://fiscaldata.treasury.gov/datasets/daily-treasury-statement/"),
    "ft900": dict(name="U.S. Census Bureau and BEA, U.S. International Trade in Goods and Services (FT-900)", url="https://www.census.gov/foreign-trade/Press-Release/current_press_release/"),
    "cbp": dict(name="U.S. Customs and Border Protection, Nationwide Encounters (CBP's file, read from the Deportation Data Project's CC0 mirror)", url="https://www.cbp.gov/document/stats/nationwide-encounters"),
    "ice_adp": dict(name="ICE Detention Statistics, monthly average daily population (compiled from ICE's files by the Deportation Data Project, CC0)", url="https://www.ice.gov/detain/detention-management"),
    "foia_removals": dict(name="ICE removal records released under FOIA to the Deportation Data Project (UC Berkeley), CC0", url="https://deportationdata.org/data/ice.html"),
}
