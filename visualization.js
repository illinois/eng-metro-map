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

  // boilerplate setup
  var margin = { top: 50, right: 50, bottom: 50, left: 50 },
     width = 960 - margin.left - margin.right,
     height = 1080 - margin.top - margin.bottom;

  var vis = d3.select('#chart')
  .append("svg")
  .attr("width", width + margin.left + margin.right)
  .attr("height", height + margin.top + margin.bottom)
  .style("width", width + margin.left + margin.right)
  .style("height", height + margin.top + margin.bottom)
  .append("g")
  .attr("transform", "translate(" + margin.left + "," + margin.top + ")");
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

    if (!edge.source.targetEdges) {
      edge.source.targetEdges = [];
    }
    edge.source.targetEdges.push(edge);

    if (!edge.target.sourceEdges) {
      edge.target.sourceEdges = [];
    }
    edge.target.sourceEdges.push(edge);
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

  // when there are multiple edges between the same two nodes, assign each edge a number
  edges.enter().each(function(d) {
    if (d.source.targetEdges) {
      let sharedEdges = d.source.targetEdges.filter(element => element.target == d.target);

      if (sharedEdges.length > 1) {
        let coLines = sharedEdges.length;
        let rank = sharedEdges.findIndex(element => element.label == d.label) + 1;
        let center = Math.ceil(coLines / 2);

        if ((coLines % 2) == 0) { // even case
          // for case of 2 lines: rank 1 should be 2 pixels above center, rank 2 be 2 pixels below center
          // for case of 4 lines: rank 1 5 pixels above, rank 2 should be 2 pixels above center, rank 3 be 2 pixels below center, rank 4 5 pixels below
          // for case of 6: 8, 5, 2; 2, 5, 8
          if (rank <= center) {
            d.y1 = d.source.y + (2 + (3 * (center - rank)));
            d.y2 = d.target.y + (2 + (3 * (center - rank)));
          } else {
            d.y1 = d.source.y - (2 + (3 * (rank - center - 1)));
            d.y2 = d.target.y - (2 + (3 * (rank - center - 1)));
          }
        } else { // odd case
          // for case of 3 lines: rank 1 should be 3 pixels above center, rank 2 should be on center, rank 3 should be 3 pixels below center
          if (rank < center) {
            d.y1 = d.source.y + (3 * (center - rank));
            d.y2 = d.target.y + (3 * (center - rank));
          }

          if (rank > center) {
            d.y1 = d.source.y - (3 * (rank - center));
            d.y2 = d.target.y - (3 * (rank - center));
          }
        }
      }
    }
  });

  // TODO: all above needs to exist before rendering -- better way for that?

  // simple tooltip to display node's name
  // TODO: fix
  var tip = d3.tip()
  .attr('class', 'd3-tip')
  .offset([-10, 0])
  .html(function(d) {
    return "<strong>" + d[name] + "</strong>";
  });

  vis.call(tip);

  // render edges
  edges.enter().append('line').attr('class', 'edge')
  .attr('x1', function(d) {
    // if (d.x1) {
    //   return d.x1;
    // }

    return d.source.x;
  })
  .attr('y1', function(d) {
    if (d.y1) {
      return d.y1;
    }

    return d.source.y;
  })
  .attr('x2', function(d) {
    // if (d.x2) {
    //   return d.x2;
    // }

    return d.target.x;
  })
  .attr('y2', function(d) {
    if (d.y2) {
      return d.y2;
    }

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
  nodes.enter().append('g').attr('class', 'node').append('circle')
  .attr('r', function(d) { // change size according to number of edges, default 5
    if (d.targetEdges && d.sourceEdges) {
      let num = (d.targetEdges.length >= d.sourceEdges.length) ? d.targetEdges.length : d.sourceEdges.length;

      if (num <= 2) {
        return 5;
      }

      return 5 + (num / 2); // TODO: optomize this
    }

    return 5;
  })
  .attr('transform', function(d) {
    return 'translate(' + d.x + ', ' + d.y + ')';
  }).append('title').text(function(d) {
      return d.name;
  })
  .on('mouseover', tip.show)
  .on('mouseout', tip.hide);
}
