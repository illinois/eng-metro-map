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
  console.log(colors);

  var vis = d3.select('#chart').attr('transform', 'translate(20, 20)');
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

  // Compute positions based on distance from root
  var setPosition = function(node, i, j, depth) {
    if (!depth) {
      depth = 0;
    }

    if (!node.x) {
      node.x = (i + 1) * 40;
      node.y = (depth + 1) * 40;

      if (depth <= 1) {
        node.edges.forEach(function(d, i2) {
          setPosition(d, i2, j, depth + 1);
        });
      }

    }
  };

  // set position for each node
  nodes.enter().each(setPosition);

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

    return colors.find(element => element.Title == d.label).Color;
  });

  // render nodes
  nodes.enter().append('g').attr('class', 'node').append('circle').attr('r', 5).attr('transform', function(d) {
    return 'translate(' + d.x + ', ' + d.y + ')';
  }).append('title').text(function(d) {
      return d.name;
  });
}
