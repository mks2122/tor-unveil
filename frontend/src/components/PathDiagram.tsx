import React, { useEffect, useRef } from 'react';
import * as d3 from 'd3';

const PathDiagram: React.FC = () => {
  const svgRef = useRef<SVGSVGElement>(null);

  useEffect(() => {
    if (!svgRef.current) return;

    const svg = d3.select(svgRef.current);
    svg.selectAll('*').remove(); // Clear previous content

    const width = 800;
    const height = 300;
    const nodeRadius = 40;

    svg.attr('width', width).attr('height', height);

    // Define nodes
    const nodes = [
      { id: 'user', label: 'User', x: 50, y: height / 2, color: '#4CAF50' },
      { id: 'guard', label: 'Guard\nNode', x: 250, y: height / 2, color: '#FF9800' },
      { id: 'middle', label: 'Middle\nNode', x: 450, y: height / 2, color: '#2196F3' },
      { id: 'exit', label: 'Exit\nNode', x: 650, y: height / 2, color: '#F44336' },
    ];

    // Draw connections
    const connections = [
      { from: nodes[0], to: nodes[1] },
      { from: nodes[1], to: nodes[2] },
      { from: nodes[2], to: nodes[3] },
    ];

    connections.forEach((conn) => {
      svg
        .append('line')
        .attr('x1', conn.from.x + nodeRadius)
        .attr('y1', conn.from.y)
        .attr('x2', conn.to.x - nodeRadius)
        .attr('y2', conn.to.y)
        .attr('stroke', '#666')
        .attr('stroke-width', 3)
        .attr('stroke-dasharray', '5,5')
        .attr('marker-end', 'url(#arrow)');
    });

    // Define arrow marker
    svg
      .append('defs')
      .append('marker')
      .attr('id', 'arrow')
      .attr('viewBox', '0 0 10 10')
      .attr('refX', 5)
      .attr('refY', 5)
      .attr('markerWidth', 6)
      .attr('markerHeight', 6)
      .attr('orient', 'auto-start-reverse')
      .append('path')
      .attr('d', 'M 0 0 L 10 5 L 0 10 z')
      .attr('fill', '#666');

    // Draw nodes
    nodes.forEach((node) => {
      const g = svg.append('g').attr('transform', `translate(${node.x},${node.y})`);

      g.append('circle')
        .attr('r', nodeRadius)
        .attr('fill', node.color)
        .attr('stroke', '#333')
        .attr('stroke-width', 2);

      g.append('text')
        .attr('text-anchor', 'middle')
        .attr('dominant-baseline', 'middle')
        .attr('fill', 'white')
        .attr('font-weight', 'bold')
        .attr('font-size', '14px')
        .selectAll('tspan')
        .data(node.label.split('\n'))
        .enter()
        .append('tspan')
        .attr('x', 0)
        .attr('dy', (d, i) => (i === 0 ? '-0.3em' : '1.2em'))
        .text((d) => d);
    });

    // Add labels
    svg
      .append('text')
      .attr('x', width / 2)
      .attr('y', 30)
      .attr('text-anchor', 'middle')
      .attr('font-size', '16px')
      .attr('font-weight', 'bold')
      .text('Conceptual Tor Circuit Path');

    svg
      .append('text')
      .attr('x', width / 2)
      .attr('y', height - 20)
      .attr('text-anchor', 'middle')
      .attr('font-size', '12px')
      .attr('fill', '#666')
      .text('Analysis focuses on correlating traffic patterns to identify probable Guard nodes');

  }, []);

  return (
    <div className="path-diagram-container">
      <h2>Circuit Path Visualization</h2>
      <div className="svg-container">
        <svg ref={svgRef}></svg>
      </div>
      <div className="diagram-explanation">
        <p>
          <strong>Guard Node (Entry):</strong> The first relay in a Tor circuit. This tool 
          attempts to identify which guard node was likely used based on traffic pattern correlation.
        </p>
        <p>
          <strong>Middle Node:</strong> Intermediate relay that helps anonymize the connection.
        </p>
        <p>
          <strong>Exit Node:</strong> The final relay that connects to the destination. 
          Traffic patterns observed here are correlated with entry patterns.
        </p>
      </div>
    </div>
  );
};

export default PathDiagram;
