// read in data and call visualize
$(function() {
  d3.json("CoEGraph.json").then(function(coordinates) {
    d3.csv("majorcolors.csv").then(function(colors) {
      d3.csv("coursecatalog.csv").then(function(courses) {
        visualize(coordinates, colors, courses);
      })
    })
  })
})

var visualize = function(data, colors, courses) {
  console.log(data);

  // boilerplate setup
  var margin = { top: 50, right: 50, bottom: 50, left: 50 },
     width = 960 - margin.left - margin.right,
     height = 1080 - margin.top - margin.bottom;

  var tip = d3.tip().attr('class', 'd3-tip')
  .offset(function(d) {
    return [-8, 0];
  })
  .html(function(d) {
    // find all colors in edge attached to a node
    let colorlist = [];
    if (d.edges) {
      colorlist = [...new Set(d.edges.map(a => a.color))];
    }

    let text = "<strong>" + d.id + "</strong><br>";

    if (d.title && d.desc && d.hours) {
      text = "<strong><i>" + d.id + ": " + d.title + "</i></strong><br>" +
      d.desc.substring(0, 51) + "... <br>" +
      "<strong>" + d.hours + "</strong>  ";
    }

    for (c of colorlist) {
      text += "<span style='color:" + c + "'> &#9679 </span>";
    }

    return text;
  });

  // TODO: make a second tooltip for edges?

  var vis = d3.select('#chart')
  .append("svg")
  .attr("width", width + margin.left + margin.right)
  .attr("height", height + margin.top + margin.bottom)
  .style("width", width + margin.left + margin.right)
  .style("height", height + margin.top + margin.bottom)
  .append("g")
  .attr("transform", "translate(" + margin.left + "," + margin.top + ")")
  .call(d3.zoom().on("zoom", function () {
    vis.attr("transform", d3.event.transform) // TODO: fix
  }))
  .call(tip);

  // add title & description to nodes based on id
  for (n of data.nodes) {
    let found = courses.find(element => (element.Subject + " " + element.Number) == n.id);

    if (n.id == "TAM 210 / 211") {
      found = courses.find(element => (element.Subject + " " + element.Number) == "TAM 211");
    }

    if (!found) {
      n.title = "";
      n.desc = "";
      n.hours = 0;
    } else {
      n.title = found.Name;
      n.desc = found.Description;
      n.hours = found["Credit Hours"];
    }
  }

  // add colors to links based on title
  for (e of data.links) {
    found = colors.find(element => element.Title == e.major);

    if (!found) {
      e.color = '#000';
    } else {
      e.color = found.Color;
    }
  }

  // TODO: remove links between the same two nodes with the same color & combine their titles


  var edges = vis.selectAll('.edge').data(data.links);
  var nodes = vis.selectAll('.node').data(data.nodes);

  // create dictionary of nodes
  var nodesDict = {};
  nodes.enter().each(function(node) {
    nodesDict[node.id] = node;
  });

  // link edges to node objects, create list of node's neighbors
  edges.enter().each(function(edge) {
    // link edge to its source and target nodes
    edge.source = nodesDict[edge.source];
    edge.target = nodesDict[edge.target];

    // add edge to the edge lists for its source and target nodes
    if (!edge.source.edges) {
      edge.source.edges = [];
    }
    edge.source.edges.push(edge);

    if (!edge.target.edges) {
      edge.target.edges = [];
    }
    edge.target.edges.push(edge);
  });

  // when there are multiple edges between the same two nodes, assign each edge a new coordinate
  edges.enter().each(function(d) { // TODO: make this better
    if (d.source.edges) {
      let sharedEdges = d.source.edges.filter(element => element.target == d.target);

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
            if (rank <= center) {
              d.y1 = d.source.y + (2 + (3 * (center - rank)));
              d.y2 = d.target.y + (2 + (3 * (center - rank)));
            } else {
              d.y1 = d.source.y - (2 + (3 * (rank - center - 1)));
              d.y2 = d.target.y - (2 + (3 * (rank - center - 1)));
            }
          } else { // odd case
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
    return d.color;
  })
  .style('stroke-width', 4);

  // render nodes
  nodes.enter().append('g').attr('class', 'node').append('circle')
  .attr('r', function(d) { // change size according to number of edges, default 5
    if (d.edges) {
      d.num = Math.ceil(d.edges.length / 2);

      if (d.num > 1) {
        d.radius = Math.ceil(((3 * (d.num)) / 2) + 1);
        return d.radius;
      }
    }

    return 4;
  })
  .attr('transform', function(d) {
    return 'translate(' + d.x + ', ' + d.y + ')';
  })
  .style('stroke-width', function(d) {
    if (d.num && (d.num > 6)) {
      return 4;
    }

    return 3;
  })
  .on('mouseover', tip.show)
  .on('mouseout', tip.hide);

  // add 'bullseye' shape for large nodes
  nodes.enter().append('g').attr('class', 'node').append('circle')
  .attr('transform', function(d) {
    return 'translate(' + d.x + ', ' + d.y + ')';
  })
  .attr('r', function(d) {
    if (d.num && d.radius) {
      if (d.num > 8) {
        return (d.radius - 10);
      }
    }

    return 0;
  })
  .style('stroke-width', function(d) {
    if (d.num && d.radius) {
      if (d.num > 8) {
        return 4;
      }
    }

    return 0;
  })
  .on('mouseover', tip.show)
  .on('mouseout', tip.hide);
}
