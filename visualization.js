// read in data and call visualize
$(function() {
  d3.json("graph.json").then(function(data) {
    d3.csv("colors/majorcolors.csv").then(function(d) {
      visualize(data, d);
    })
  })
})

var visualize = function(data, colors) {
  console.log(data);

  var vis = d3.select('#chart').append("svg").attr('transform', 'translate(20, 20)').append("g");
  var edges = vis.selectAll('.edge').data(data.edges);
  var nodes = vis.selectAll('.node').data(data.nodes);

  // create dictionary of nodes
  var nodesDict = {};
  nodes.enter().each(function(d) {
    nodesDict[d.name] = d;
  });

  // link edges to node objects, create list of node's neighbors
  edges.enter().each(function(edge) {
    edge.source = nodesDict[edge.source];
    edge.target = nodesDict[edge.target];

    if (!edge.source.edges) {
      edge.source.edges = [];
    }
    edge.source.edges.push(edge.target);

    if (!edge.target.edges) {
      edge.target.edges = [];
    }
    edge.target.edges.push(edge.source);
  });

  // Compute positions based for nodes based on the major they are a part of
  // major # (i) corresponds to y position, course # (j) corresponds to x position
  for (let i = 0; i < data.majors.length; i++) {
    for (let j = 0; j < data.majors[i].courses.length; j++) {
      if (!nodesDict[data.majors[i].courses[j]].x) { // only set positions for nodes that haven't been set
        nodesDict[data.majors[i].courses[j]].x = (j + 1) * 40;
        nodesDict[data.majors[i].courses[j]].y = (i + 1) * 40;
      }
    }
  }

  // simple tooltip to display node's name
  var tip = d3.tip()
  .attr('class', 'd3-tip')
  .offset([-10, 0])
  .html(function(d) {
    return "<strong>" + d[name] + "</strong>";
  });

  vis.call(tip);

  // render edges
  edges.enter().append('line').attr('class', 'edge').attr('x1', function(d) {
    return d.source.x;
  }).attr('y1', function(d) {
    return d.source.y;
  }).attr('x2', function(d) {
    return d.target.x;
  }).attr('y2', function(d) {
    return d.target.y;
  })
  .attr('stroke', function(d) { // make edge color the major's color
    found = colors.find(element => element.Title == d.label);

    if (!found) {
      return '#000';
    }

    return found.Color;
  });

  // render nodes
  nodes.enter().append('g').attr('class', 'node').append('circle').attr('r', 5).attr('transform', function(d) {
    return 'translate(' + d.x + ', ' + d.y + ')';
  }).append('title').text(function(d) {
      return d.name;
  })
  .on('mouseover', tip.show)
  .on('mouseout', tip.hide);
}
