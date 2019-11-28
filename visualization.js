// read in data and call visualize
$(function() {
  d3.json("CSMap.JSON").then(function(data) {
    visualize(data);
  })
})

var visualize = function(data) {
  console.log(data);

  var vis = d3.select('#chart').attr('transform', 'translate(20, 20)');
  var links = vis.selectAll('.link').data(data.links);
  var nodes = vis.selectAll('.node').data(data.nodes);

  // Store nodes in a hash by name
  var nodesByName = {};
  // why do these .each()s need .enter() before them??
  nodes.enter().each(function(d) {
    nodesByName[d.name] = d;
  });

  // Convert link references to objects
  links.enter().each(function(link) {
      link.source = nodesByName[link.source];
      link.target = nodesByName[link.target];
      if (!link.source.links) {
          link.source.links = [];
      }
      link.source.links.push(link.target);
      if (!link.target.links) {
          link.target.links = [];
      }
      link.target.links.push(link.source);
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
              node.links.forEach(function(d, i2) {
                  setPosition(d, i2, j, depth + 1);
              });
          }

      }
  };
  nodes.enter().each(setPosition);

  links.enter().append('line').attr('class', 'link').attr('x1', function(d) {
    return d.source.x;
  }).attr('y1', function(d) {
    return d.source.y;
  }).attr('x2', function(d) {
    return d.target.x;
  }).attr('y2', function(d) {
    return d.target.y;
  });

  nodes.enter().append('g').attr('class', 'node').append('circle').attr('r', 5).attr('transform', function(d) {
    return 'translate(' + d.x + ', ' + d.y + ')';
  }).append('title').text(function(d) {
      return d.name;
  });
}
