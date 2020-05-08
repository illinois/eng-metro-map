// read in data and call visualize
$(function() {
  d3.json("CoEGraph.json").then(function(coordinates) {
    d3.csv("majorcolors.csv").then(function(colors) {
      d3.csv("coursecatalog.csv").then(function(courses) {
        process(coordinates, colors, courses);
      })
    })
  })
})

var process = function(data, colors, courses) {
  // create dictionary of nodes
  var nodesDict = {};

  // add nodes to dict, add title & description to nodes based on id
  for (n of data.nodes) {
    n.y = (n.y - 195);

    nodesDict[n.id] = n;

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

  for (e of data.links) {
    // add colors to links based on title
    found = colors.find(element => element.Title == e.major);

    if (!found) {
      e.color = '#000';
    } else {
      e.color = found.Color;
    }

    // link edges to node objects
    // link edge to its source and target nodes
    e.source = nodesDict[e.source];
    e.target = nodesDict[e.target];

    // create ordered list of nodes connected to
    e.between = [e.source.id, e.target.id].sort();

    // add edge to the edge lists for its source and target nodes
    if (!e.source.edges) {
      e.source.edges = [];
    }
    e.source.edges.push(e);

    if (!e.target.edges) {
      e.target.edges = [];
    }
    e.target.edges.push(e);
  }

  // remove links between the same two nodes with the same color & combine titles
  let edgegroups = _.groupBy(data.links, "between");
  for (i in edgegroups) {
    if (edgegroups[i].length > 1) {
      let colorgroups = _.groupBy(edgegroups[i], "color");
      for (j in colorgroups) {
        if (colorgroups[j].length > 1) {
          let newtitle = colorgroups[j][0].major;
          for (k = 1; k < colorgroups[j].length; k++) {
            // add title to master title
            newtitle += " and " + colorgroups[j][k].major;

            // remove from links
            let index = data.links.indexOf(colorgroups[j][k]);
            if (index > -1) {
              data.links.splice(index, 1);
            } else {
              console.log("uhh");
            }
          }

          // adjust title
          let index = data.links.indexOf(colorgroups[j][0]);
          if (index > -1) {
            data.links[index].major = newtitle;
          } else {
            console.log("uhh");
          }
        }
      }
    }
  }

  // create new coordinates to layer lines
  edgegroups = _.groupBy(data.links, "between");
  console.log(edgegroups);
  for (i in edgegroups) {
    if (edgegroups[i].length > 1) {
      for (j = 0; j < edgegroups[i].length; j++) {
        let center = Math.ceil(edgegroups[i].length / 2);
        let index = data.links.indexOf(edgegroups[i][j]);

        if (((edgegroups[i][j].source.x - edgegroups[i][j].target.x) == 0) || (Math.abs((edgegroups[i][j].source.y - edgegroups[i][j].target.y) / (edgegroups[i][j].source.x - edgegroups[i][j].target.x)) > 1)) { // vertical
          if ((edgegroups[i].length % 2) == 0) { // even
            if ((j + 1) < center) { // -
              data.links[index].x1 = data.links[index].source.x - (4 * (center - (j + 1))) - 2;
              data.links[index].x2 = data.links[index].target.x - (4 * (center - (j + 1))) - 2;
            } else { // +
              data.links[index].x1 = data.links[index].source.x + (4 * ((j + 1) - center)) - 2;
              data.links[index].x2 = data.links[index].target.x + (4 * ((j + 1) - center)) - 2;
            }
          } else { // odd
            if ((j + 1) < center) { // -
              data.links[index].x1 = data.links[index].source.x - (4 * (center - (j + 1)));
              data.links[index].x2 = data.links[index].target.x - (4 * (center - (j + 1)));
            } else { // +
              data.links[index].x1 = data.links[index].source.x + (4 * ((j + 1) - center));
              data.links[index].x2 = data.links[index].target.x + (4 * ((j + 1) - center));
            }
          }
        } else { // horizontal
          if ((edgegroups[i].length % 2) == 0) { // even
            if ((j + 1) < center) { // -
              data.links[index].y1 = data.links[index].source.y - (4 * (center - (j + 1))) - 2;
              data.links[index].y2 = data.links[index].target.y - (4 * (center - (j + 1))) - 2;
            } else { // +
              data.links[index].y1 = data.links[index].source.y + (4 * ((j + 1) - center)) - 2;
              data.links[index].y2 = data.links[index].target.y + (4 * ((j + 1) - center)) - 2;
            }
          } else { // odd
            if ((j + 1) < center) { // -
              data.links[index].y1 = data.links[index].source.y - (4 * (center - (j + 1)));
              data.links[index].y2 = data.links[index].target.y - (4 * (center - (j + 1)));
            } else { // +
              data.links[index].y1 = data.links[index].source.y + (4 * ((j + 1) - center));
              data.links[index].y2 = data.links[index].target.y + (4 * ((j + 1) - center));
            }
          }
        }
      }
    }
  }

  visualize(data, colors, courses, nodesDict);
};

var visualize = function(data, colors, courses, nodesDict) {
  console.log(data);

  // Find the width of the area where the `svg` will be placed:
  let client_width = $("#sizer").width();

  // Scale the visualization based on a scale of the size and the width of the rendered content:
  let scale_factor = client_width / 2000;

  // boilerplate setup
  var margin = { top: 50, right: 50, bottom: 50, left: 50 },
     width = client_width - margin.left - margin.right,
     height = 1000 - margin.top - margin.bottom; // scale height???

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

  var vis = d3.select('#chart')
  .append("svg")
  .attr("width", width + margin.left + margin.right)
  .attr("height", height + margin.top + margin.bottom)
  .style("width", width + margin.left + margin.right)
  .style("height", height + margin.top + margin.bottom)
  .append("g")
  .attr("transform", "scale(" + scale_factor + ")")
  .append("g")
  .attr("transform", "translate(" + margin.left + "," + margin.top + ")")
  .call(d3.zoom().on("zoom", function () {
    vis.attr("transform", d3.event.transform)
  }))
  .call(tip);

  var top = 3;
  var textx = 150;
  var linestart = 0;
  var lineend = 130;
  var factor = 22;

  vis.append('text').text('Aerospace Engineering').attr('class', 'majortext')
    .attr('x', textx)
    .attr('y', top + 10);

  vis.append('line').attr('stroke', '#ef2722').style('stroke-width', 8)
    .attr('x1', linestart)
    .attr('y1', top + 6)
    .attr('x2', lineend)
    .attr('y2', top + 6);

  vis.append('text').text('Agricultural and Biological Engineering').attr('class', 'majortext')
    .attr('x', textx)
    .attr('y', top + 10 + factor);

  vis.append('line').attr('stroke', '#fdde33').style('stroke-width', 8)
    .attr('x1', linestart)
    .attr('y1', (top + 10 + factor) - 6)
    .attr('x2', lineend)
    .attr('y2', (top + 10 + factor) - 6);

  vis.append('text').text('Bioengineering').attr('class', 'majortext')
    .attr('x', textx)
    .attr('y', top + 10 + (factor * 2));

  vis.append('line').attr('stroke', '#f088a1').style('stroke-width', 8)
    .attr('x1', linestart)
    .attr('y1', (top + 10 + (factor * 2)) - 6)
    .attr('x2', lineend)
    .attr('y2', (top + 10 + (factor * 2)) - 6);

  vis.append('text').text('Chemical and Biomolecular Engineering').attr('class', 'majortext')
    .attr('x', textx)
    .attr('y', top + 10 + (factor * 3));

  vis.append('line').attr('stroke', '#990b5d').style('stroke-width', 8)
    .attr('x1', linestart)
    .attr('y1', (top + 10 + (factor * 3)) - 6)
    .attr('x2', lineend)
    .attr('y2', (top + 10 + (factor * 3)) - 6);

  vis.append('text').text('Civil Engineering').attr('class', 'majortext')
    .attr('x', textx)
    .attr('y', top + 10 + (factor * 4));

  vis.append('line').attr('stroke', '#ad611d').style('stroke-width', 8)
    .attr('x1', linestart)
    .attr('y1', (top + 10 + (factor * 4)) - 6)
    .attr('x2', lineend)
    .attr('y2', (top + 10 + (factor * 4)) - 6);

  vis.append('text').text('Computer Engineering').attr('class', 'majortext')
    .attr('x', textx)
    .attr('y', top + 10 + (factor * 5));

  vis.append('line').attr('stroke', '#7fccba').style('stroke-width', 8)
    .attr('x1', linestart)
    .attr('y1', (top + 10 + (factor * 5)) - 6)
    .attr('x2', lineend)
    .attr('y2', (top + 10 + (factor * 5)) - 6);

  vis.append('text').text('Electrical Engineering').attr('class', 'majortext')
    .attr('x', textx)
    .attr('y', top + 10 + (factor * 6));

  vis.append('line').attr('stroke', '#0e707c').style('stroke-width', 8)
    .attr('x1', linestart)
    .attr('y1', (top + 10 + (factor * 6)) - 6)
    .attr('x2', lineend)
    .attr('y2', (top + 10 + (factor * 6)) - 6);

  vis.append('text').text('Computer Science').attr('class', 'majortext')
    .attr('x', textx)
    .attr('y', top + 10 + (factor * 7));

  vis.append('line').attr('stroke', '#1aa0da').style('stroke-width', 8)
    .attr('x1', linestart)
    .attr('y1', (top + 10 + (factor * 7)) - 6)
    .attr('x2', lineend)
    .attr('y2', (top + 10 + (factor * 7)) - 6);

  vis.append('text').text('Engineering Mechanics').attr('class', 'majortext')
    .attr('x', textx)
    .attr('y', top + 10 + (factor * 8));

  vis.append('line').attr('stroke', '#f38035').style('stroke-width', 8)
    .attr('x1', linestart)
    .attr('y1', (top + 10 + (factor * 8)) - 6)
    .attr('x2', lineend)
    .attr('y2', (top + 10 + (factor * 8)) - 6);

  vis.append('text').text('Engineering Physics').attr('class', 'majortext')
    .attr('x', textx)
    .attr('y', top + 10 + (factor * 9));

  vis.append('line').attr('stroke', '#90999f').style('stroke-width', 8)
    .attr('x1', linestart)
    .attr('y1', (top + 10 + (factor * 9)) - 6)
    .attr('x2', lineend)
    .attr('y2', (top + 10 + (factor * 9)) - 6);

  vis.append('text').text('Industrial Engineering').attr('class', 'majortext')
    .attr('x', textx)
    .attr('y', top + 10 + (factor * 10));

  vis.append('line').attr('stroke', '#16995d').style('stroke-width', 8)
    .attr('x1', linestart)
    .attr('y1', (top + 10 + (factor * 10)) - 6)
    .attr('x2', lineend)
    .attr('y2', (top + 10 + (factor * 10)) - 6);

  vis.append('text').text('Materials Science and Engineering').attr('class', 'majortext')
    .attr('x', textx)
    .attr('y', top + 10 + (factor * 11));

  vis.append('line').attr('stroke', '#224697').style('stroke-width', 8)
    .attr('x1', linestart)
    .attr('y1', (top + 10 + (factor * 11)) - 6)
    .attr('x2', lineend)
    .attr('y2', (top + 10 + (factor * 11)) - 6);

  vis.append('text').text('Mechanical Engineering').attr('class', 'majortext')
    .attr('x', textx)
    .attr('y', top + 10 + (factor * 12));

  vis.append('line').attr('stroke', '#f5a72f').style('stroke-width', 8)
    .attr('x1', linestart)
    .attr('y1', (top + 10 + (factor * 12)) - 6)
    .attr('x2', lineend)
    .attr('y2', (top + 10 + (factor * 12)) - 6);

  vis.append('text').text('Nuclear, Plasma, and Radiological Engineering').attr('class', 'majortext')
    .attr('x', textx)
    .attr('y', top + 10 + (factor * 13));

  vis.append('line').attr('stroke', '#7abd31').style('stroke-width', 8)
    .attr('x1', linestart)
    .attr('y1', (top + 10 + (factor * 13)) - 6)
    .attr('x2', lineend)
    .attr('y2', (top + 10 + (factor * 13)) - 6);

  vis.append('text').text('Systems Engineering').attr('class', 'majortext')
    .attr('x', textx)
    .attr('y', top + 10 + (factor * 14));

  vis.append('line').attr('stroke', '#000').style('stroke-width', 8)
    .attr('x1', linestart)
    .attr('y1', (top + 10 + (factor * 14)) - 6)
    .attr('x2', lineend)
    .attr('y2', (top + 10 + (factor * 14)) - 6);

  var edges = vis.selectAll('.edge').data(data.links);
  var nodes = vis.selectAll('.node').data(data.nodes);

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
