// read in data and call visualize
$(function() {
  d3.json("12.json").then(function(data) {
    d3.csv("majorcolors.csv").then(function(d) {
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

  var edges = vis.selectAll('.edge').data(data.links);
  var nodes = vis.selectAll('.node').data(data.nodes);

  // create dictionary of nodes
  var nodesDict = {};
  nodes.enter().each(function(d) {
    d.x = (d.x * 1 - 500);
    d.y = (d.y * 1 - 400);
    nodesDict[d.id] = d;
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

  // when there are multiple edges between the same two nodes, assign each edge a new coordinate
  edges.enter().each(function(d) {
    if (d.source.targetEdges) {
      let sharedEdges = d.source.targetEdges.filter(element => element.target == d.target);

      if (sharedEdges.length > 1) {
        let coLines = sharedEdges.length;
        let rank = sharedEdges.findIndex(element => element.major == d.major) + 1;
        let center = Math.ceil(coLines / 2);

        if (((d.source.x - d.target.x) == 0) || (Math.abs((d.source.y - d.target.y) / (d.source.x - d.target.x)) > 1)) { // vertical case
          if ((coLines % 2) == 0) {
            if (rank <= center) {
              d.x1 = d.source.x - (2 + (3 * (center - rank)));
              d.x2 = d.target.x - (2 + (3 * (center - rank)));
            } else {
              d.x1 = d.source.x + (2 + (3 * (rank - center - 1)));
              d.x2 = d.target.x + (2 + (3 * (rank - center - 1)));
            }
          } else {
            if (rank < center) {
              d.x1 = d.source.x - (3 * (center - rank));
              d.x2 = d.target.x - (3 * (center - rank));
            } else {
              d.x1 = d.source.x + (3 * (rank - center));
              d.x2 = d.target.x + (3 * (rank - center));
            }
          }
        } else { // horizontal case
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
            } else {
              d.y1 = d.source.y - (3 * (rank - center));
              d.y2 = d.target.y - (3 * (rank - center));
            }
          }
        }
      }
    }
  });

  // render edges
  edges.enter().append('line').attr('class', 'edge')
  .attr('x1', function(d) {
    if (d.x1) {
      return d.x1;
    }

    return d.source.x;
  })
  .attr('y1', function(d) {
    if (d.y1) {
      return d.y1;
    }

    return d.source.y;
  })
  .attr('x2', function(d) {
    if (d.x2) {
      return d.x2;
    }

    return d.target.x;
  })
  .attr('y2', function(d) {
    if (d.y2) {
      return d.y2;
    }

    return d.target.y;
  })
  .attr('stroke', function(d) { // make edge color the major's color
    found = colors.find(element => element.Title == d.major);

    if (!found) {
      return '#000';
    }

    console.log(found.Color);
    return found.Color;
  });

  // render nodes
  nodes.enter().append('g').attr('class', 'node').append('circle')
  .attr('r', function(d) { // change size according to number of edges, default 5
    if (d.targetEdges && d.sourceEdges) {
      let num = (d.targetEdges.length + d.sourceEdges.length) / 2;

      if (num > 2) {
        return 5 + (num / 2);
      }
    }

    return 5;
  })
  .attr('transform', function(d) {
    return 'translate(' + d.x + ', ' + d.y + ')';
  }).append('title').text(function(d) {
      return d.id;
  });
}
