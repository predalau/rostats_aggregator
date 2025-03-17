<template>
  <div id="app">
    <!-- Header -->
    <header>
      <h1>Romania Public Statistics Dashboard</h1>
      <nav>
        <ul>
          <li><a href="#">Home</a></li>
          <li><a href="#">About</a></li>
          <li><a href="#">Contact</a></li>
        </ul>
      </nav>
      <button @click="login">Login</button>
    </header>

    <!-- Main Content -->
    <main>
      <div id="chart"></div>
    </main>
  </div>
</template>

<script>
import Plotly from "plotly.js-dist";

export default {
  name: "App",
  methods: {
    login() {
      alert("Login button clicked!");
    },
  },
  mounted() {
    // Create the Plotly chart
    const data = [
      {
        x: [2020, 2021, 2022],
        y: [19237691, 19119880, 19000000],
        type: "bar",
        name: "Population",
      },
    ];

    const layout = {
      title: "Population Over Time",
      xaxis: { title: "Year" },
      yaxis: { title: "Population" },
    };

    Plotly.newPlot("chart", data, layout);
  },
};
</script>

<style>
/* Basic Styling */
body {
  font-family: Arial, sans-serif;
  margin: 0;
  padding: 0;
  background-color: #f4f4f4;
}

header {
  background-color: #333;
  color: white;
  padding: 1rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

header h1 {
  margin: 0;
}

nav ul {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
}

nav ul li {
  margin: 0 1rem;
}

nav ul li a {
  color: white;
  text-decoration: none;
}

nav ul li a:hover {
  text-decoration: underline;
}

button {
  background-color: #4caf50;
  color: white;
  border: none;
  padding: 0.5rem 1rem;
  cursor: pointer;
}

button:hover {
  background-color: #45a049;
}

main {
  padding: 2rem;
}

#chart {
  width: 100%;
  height: 400px;
}
</style>
