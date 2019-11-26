// read in data and call visualize
// $(function() {
//   d3.json("CSMap.JSON").then(function(data) {
//     visualize(data);
//   })
// })

var data = {
  nodes: [{
    name: "CS 100"
  },
  {
    name: "ENG 100"
  },
  {
    name: "MATH 221"
  }],
  edges: [{
    source: "CS 100",
    target: "ENG 100",
    label: "Computer Science"
  },
  {
    source: "ENG 100",
    target: "MATH 221",
    label: "Computer Science"
  }]
}

var visualize = function(data) {
  console.log(data);

  var margin = { top: 50, right: 50, bottom: 50, left: 50 };
  var width = 960 - margin.left - margin.right;
  var height = 960 - margin.top - margin.bottom;

  var svg = d3.select("#chart")
  .append("svg")
  .attr("width", width + margin.left + margin.right)
  .attr("height", height + margin.top + margin.bottom)
  .style("width", width + margin.left + margin.right)
  .style("height", height + margin.top + margin.bottom)

  var g = svg.append("g")
  .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

  // create graph edges
  
}
