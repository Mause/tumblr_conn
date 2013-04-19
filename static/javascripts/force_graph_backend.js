var initialise_graph = function(filename){
    "use strict";
    var width = document.width-50,
        height = document.height-50;

    var color = d3.scale.category20();

    var force = d3.layout.force()
        .charge(-120)
        .linkDistance(30)
        .size([width, height]);

    var svg = d3.select("body").append("svg")
        .attr("width", width)
        .attr("height", height);

    d3.json(filename, function(error, graph) {
        if (error) console.error(error);

        force
            .nodes(graph.nodes)
            .links(graph.links)
            .start();

        var link = svg.selectAll("line.link")
            .data(graph.links)
            .enter().append("line")
            .attr("class", "link")
            .style("stroke-width", function(d) { return Math.sqrt(d.value); });

        var node = svg.selectAll("circle.node")
            .data(graph.nodes)
            .enter().append("circle")
            .attr("class", "node")
            .attr("r", function(d){ return d.weight; })
            .style("fill", function(d) { return color(d.blog_id); })
            .call(force.drag);

        node.append("title")
            .text(function(d) { return d.blog_name; });

        force.on("tick", function() {
            link.attr("x1", function(d) { return d.source.x; })
                .attr("y1", function(d) { return d.source.y; })
                .attr("x2", function(d) { return d.target.x; })
                .attr("y2", function(d) { return d.target.y; });

            node.attr("cx", function(d) { return d.x; })
                .attr("cy", function(d) { return d.y; });
        });
    });
};
var filename = getURLParameter('filename');
if (!filename) {
    console.error('The filename variable must be a scope accessable to the initialise_graph function call');
    initialise_graph('http://localhost:8888/static/example.json');
} else {
    filename = '/graph/force/graph_data?blog_name=' + toString(filename);
    initialise_graph(filename);
}
