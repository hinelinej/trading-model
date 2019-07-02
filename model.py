import random
import json
        
# Percent chance that a given symbol's growth wedge will invert (ascending vs descending).
# This progressively increases until the wedge is inverted.
INVERSION_PROGRESSION_CHANCE = .225 

# These determine the range of slopes that can be generated for the wedges; measured in basis points.
MINOR_SLOPE_MINIMUM = 200 # 2%
MINOR_SLOPE_MAXIMUM = 500 # 5%
MODERATE_SLOPE_MINIMUM = 400 # 4%
MODERATE_SLOPE_MAXIMUM = 1200 # 12%

# These determine the range of heights of the left side of the wedges; measured in basis points
WEDGE_START_MINIMUM = 300 # 3%
WEDGE_START_MAXIMUM = 600 # 6%

# These determine the range of durations a given wedge can have; measured in days
WEDGE_DURATION_MINIMUM = 10
WEDGE_DURATION_MAXIMUM = 30

# These determine the starting price of a given symbol.
MINIMUM_STARTING_PRICE = 100.
MAXIMUM_STARTING_PRICE = 10000.

# Representation of digital currency
class Symbol(object):
    def __init__(self, symbol):
        self.symbol = symbol

        # Set up the starting price
        self.current_price = 1. * random.randrange(MINIMUM_STARTING_PRICE, MAXIMUM_STARTING_PRICE)
        self.history = [self.current_price]

        # Generate the first wedge
        self.inversion_chance = 0.
        self.wedge_direction = random.randrange(0, 2) == 0
        self.generateWedge()

    # Generates a new wedge
    def generateWedge(self):
        # We generate two slopes, one minor and one moderate. If we are generating an
        # ascending wedge, they will be positive slopes stacked minor / moderate. If
        # it is a descending wedge, they will be negative and stacked moderate / minor.

        slope1 = random.randrange(MINOR_SLOPE_MINIMUM, MINOR_SLOPE_MAXIMUM) / 10000.
        slope2 = random.randrange(MODERATE_SLOPE_MINIMUM, MODERATE_SLOPE_MAXIMUM) / 10000.
        duration = random.randrange(WEDGE_DURATION_MINIMUM, WEDGE_DURATION_MAXIMUM)

        # We're generating an ascending wedge
        if self.wedge_direction:
            upper_slope = 1 + slope1
            lower_slope = 1 + slope2
        else:
            upper_slope = 1 - slope2
            lower_slope = 1 - slope1

        # Determine the start and end points for the wedge boundaries
        wedge_start = random.randrange(WEDGE_START_MINIMUM, WEDGE_START_MAXIMUM) / 10000.
        upper_boundary_start = (1 + wedge_start) * self.current_price
        upper_boundary_delta = upper_boundary_start - (upper_boundary_start * upper_slope)
        lower_boundary_start = (1 - wedge_start) * self.current_price
        lower_boundary_delta = lower_boundary_start - (lower_boundary_start * lower_slope)

        # Then generate the maxima and minima for each tick
        self.maxima = [upper_boundary_start + (upper_boundary_delta * tick / duration) for tick in range(1, duration + 1)]
        self.minima = [lower_boundary_start + (lower_boundary_delta * tick / duration) for tick in range(1, duration + 1)]

    # Updates the value of this symbol according to its wedge, regenerating the wedge
    # if necessary.
    def update(self):
        # Generate a new value somewhere between the current tick's maxima and minima
        price = round(random.randrange(self.minima[0], self.maxima[0], 1, float), 2)

        self.history.append(price)
        self.current_price = price

        # Cleanup
        del self.maxima[0]
        del self.minima[0]

        # We finished out this wedge so generate a new one. First we need to check for inversion.
        if len(self.maxima) == 0:
            self.inversion_chance += INVERSION_PROGRESSION_CHANCE
            if self.inversion_chance >= random.randrange(0, 1 / INVERSION_PROGRESSION_CHANCE**2, 1, float):
                # We are inverting the wedge
                self.wedge_direction = not self.wedge_direction

                # Reset the inversion chance
                self.inversion_chance = 0

            # Regnerate the wedge
            self.generateWedge()

# generates the output HTML
def generateHTML(symbols):
    return """
<html>
    <head>
        <style>
        .chart {
          width: 80%;
          height: 350px;
          margin: 0 auto;
          margin-bottom: 2em;
        }

        </style>
    </head>
    <body>
        <script src="https://www.amcharts.com/lib/4/core.js"></script>
        <script src="https://www.amcharts.com/lib/4/charts.js"></script>
        <script src="https://www.amcharts.com/lib/4/themes/animated.js"></script>

        <script>
            // Set up charts
            am4core.ready(function() {
                am4core.useTheme(am4themes_animated);
                
                const symbols = """ + json.dumps(map(lambda symbol: symbol.symbol, symbols)) + """;
                const data = """ + json.dumps(map(lambda symbol: symbol.history, symbols)) + """;

                // Generate charts
                for (let i = 0; i < data.length; i ++) {
                    const chartDiv = document.createElement("DIV");
                    chartDiv.id = `chart-${i}`;
                    chartDiv.classList.add("chart");
                    document.body.appendChild(chartDiv);
                    chart = am4core.create(`chart-${i}`, am4charts.XYChart)

                    const firstDate = new Date();
                    firstDate.setDate(firstDate.getDate() - data[0].length);
                    chart.data = data[i].map((price, index) => {
                        const newDate = new Date(firstDate);
                        newDate.setDate(newDate.getDate() + index);

                        return {
                            date : newDate,
                            price : price,
                        };
                    });
                    console.log(chart.data);

                    // Create axes
                    var dateAxis = chart.xAxes.push(new am4charts.DateAxis());
                    dateAxis.renderer.minGridDistance = 50;

                    var valueAxis = chart.yAxes.push(new am4charts.ValueAxis());

                    // Create title
                    const title = chart.titles.create();
                    title.text = symbols[i];
                    title.fontSize = 25;
                    title.marginBottom = 30;

                    // Create series
                    var series = chart.series.push(new am4charts.LineSeries());
                    series.dataFields.valueY = "price";
                    series.dataFields.dateX = "date";
                    series.strokeWidth = 2;
                    series.minBulletDistance = 10;
                    series.tooltipText = "{valueY}";
                    series.tooltip.pointerOrientation = "vertical";
                    series.tooltip.background.cornerRadius = 20;
                    series.tooltip.background.fillOpacity = 0.5;
                    series.tooltip.label.padding(12,12,12,12)

                    // Add scrollbar
                    chart.scrollbarX = new am4charts.XYChartScrollbar();
                    chart.scrollbarX.series.push(series);

                    // Add cursor
                    chart.cursor = new am4charts.XYCursor();
                    chart.cursor.xAxis = dateAxis;
                    chart.cursor.snapToSeries = series;
                }

            });
        </script>
    </body>
</html>
"""

# Generates a list of unique three letter symbols
def generateSymbols(count):
    symbols = []
    
    while len(symbols) < count:
        symbol = "".join([chr(random.randrange(65, 65 + 26)) for _ in range(3)])

        if symbol not in symbols:
            symbols.append(Symbol(symbol))

    return symbols

# Generate some symbols
symbols = generateSymbols(3)

# Generate some data
for tick in range(10000):
    for symbol in symbols:
        symbol.update()

# Output the results
with open("output.csv", "w") as f:
    f.write(",".join(map(lambda symbol: symbol.symbol, symbols)) + "\n")
    for tick in range(len(symbols[0].history)):
        f.write(",".join(map(lambda symbol: "%0.2f" % symbol.history[tick], symbols)) + "\n")

with open("output.html", "w") as f:
    f.write(generateHTML(symbols))
