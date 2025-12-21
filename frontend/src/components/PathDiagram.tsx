import React, { useEffect, useRef } from 'react';
import * as d3 from 'd3';

interface PathDiagramProps {
  entryNode?: string;
  exitNode?: string;
  entryCountry?: string;
  entryCountryName?: string;
}

const PathDiagram: React.FC<PathDiagramProps> = ({ entryNode, exitNode, entryCountry, entryCountryName }) => {
  const svgRef = useRef<SVGSVGElement>(null);

  useEffect(() => {
    if (!svgRef.current) return;

    const svg = d3.select(svgRef.current);
    svg.selectAll('*').remove(); // Clear previous content

    const width = 950;
    const height = 380;
    const nodeRadius = 55;

    svg.attr('width', width).attr('height', height);

    // Define nodes with better spacing
    const nodes = [
      { id: 'user', label: entryNode ? `User\nSource` : 'User', x: 90, y: height / 2, color: '#27ae60', icon: '👤', size: nodeRadius * 0.9 },
      { id: 'guard', label: entryNode ? `Guard\n${entryNode.substring(0, 8)}...` : 'Guard\nNode', x: 310, y: height / 2, color: '#e67e22', icon: '🛡️', highlighted: !!entryNode, size: nodeRadius },
      { id: 'middle', label: 'Middle\nRelay', x: 550, y: height / 2, color: '#3498db', icon: '🔄', size: nodeRadius * 0.95 },
      { id: 'exit', label: exitNode ? `Exit\n${exitNode.substring(0, 8)}...` : 'Exit\nNode', x: 790, y: height / 2, color: '#e74c3c', icon: '🚪', highlighted: !!exitNode, size: nodeRadius },
    ];

    // Define arrow marker FIRST (before connections)
    const defs = svg.append('defs');
    
    defs.append('marker')
      .attr('id', 'arrow')
      .attr('viewBox', '0 0 10 10')
      .attr('refX', 9)
      .attr('refY', 5)
      .attr('markerWidth', 8)
      .attr('markerHeight', 8)
      .attr('orient', 'auto-start-reverse')
      .append('path')
      .attr('d', 'M 0 0 L 10 5 L 0 10 z')
      .attr('fill', '#9b59b6');

    // Define gradient for connections
    const gradient = defs
      .append('linearGradient')
      .attr('id', 'connection-gradient')
      .attr('x1', '0%')
      .attr('y1', '0%')
      .attr('x2', '100%')
      .attr('y2', '0%');
    
    // Draw connections with animation
    const connections = [
      { from: nodes[0], to: nodes[1], label: 'Encrypted\nLayer 1' },
      { from: nodes[1], to: nodes[2], label: 'Encrypted\nLayer 2' },
      { from: nodes[2], to: nodes[3], label: 'Encrypted\nLayer 3' },
    ];
    
    gradient.append('stop')
      .attr('offset', '0%')
      .attr('stop-color', '#3498db')
      .attr('stop-opacity', 0.8);
    
    gradient.append('stop')
      .attr('offset', '100%')
      .attr('stop-color', '#9b59b6')
      .attr('stop-opacity', 0.8);

    connections.forEach((conn, idx) => {
      // Animated dashed line
      const line = svg
        .append('line')
        .attr('x1', conn.from.x + (conn.from.size || nodeRadius))
        .attr('y1', conn.from.y)
        .attr('x2', conn.to.x - (conn.to.size || nodeRadius))
        .attr('y2', conn.to.y)
        .attr('stroke', 'url(#connection-gradient)')
        .attr('stroke-width', 5)
        .attr('stroke-dasharray', '10,6')
        .attr('marker-end', 'url(#arrow)')
        .attr('opacity', 0)
        .transition()
        .delay(idx * 250)
        .duration(600)
        .attr('opacity', 0.8);
      
      // Animate dash offset for flowing effect
      line.node()?.setAttribute('stroke-dashoffset', '0');
      
      svg.select('line')
        .transition()
        .duration(2000)
        .ease(d3.easeLinear)
        .attr('stroke-dashoffset', '-16')
        .on('end', function repeat() {
          d3.select(this)
            .transition()
            .duration(2000)
            .ease(d3.easeLinear)
            .attr('stroke-dashoffset', '-32')
            .on('end', repeat);
        });

      // Add connection labels with background
      const midX = (conn.from.x + conn.to.x) / 2;
      const labelGroup = svg.append('g')
        .attr('opacity', 0);
      
      // Background rectangle for label
      labelGroup.append('rect')
        .attr('x', midX - 70)
        .attr('y', conn.from.y - 62)
        .attr('width', 140)
        .attr('height', 32)
        .attr('rx', 5)
        .attr('fill', 'rgba(236, 240, 241, 0.95)')
        .attr('stroke', '#95a5a6')
        .attr('stroke-width', 1.5);
      
      labelGroup.append('text')
        .attr('x', midX)
        .attr('y', conn.from.y - 52)
        .attr('text-anchor', 'middle')
        .attr('font-size', '11.5px')
        .attr('fill', '#34495e')
        .attr('font-weight', '600')
        .text(conn.label.split('\n')[0]);
      
      labelGroup.append('text')
        .attr('x', midX)
        .attr('y', conn.from.y - 38)
        .attr('text-anchor', 'middle')
        .attr('font-size', '11.5px')
        .attr('fill', '#34495e')
        .attr('font-weight', '600')
        .text(conn.label.split('\n')[1]);
        
      labelGroup
        .transition()
        .delay(idx * 250 + 400)
        .duration(600)
        .attr('opacity', 1);
    });
    
    // Add legend
    const legendData = [
      { color: '#27ae60', label: 'Source', icon: '\ud83d\udc64' },
      { color: '#e67e22', label: 'Entry Guard (ID)', icon: '\ud83d\udee1\ufe0f' },
      { color: '#3498db', label: 'Middle Relay', icon: '\ud83d\udd04' },
      { color: '#e74c3c', label: 'Exit Node', icon: '\ud83d\udeaa' }
    ];
    
    const legend = svg.append('g')
      .attr('transform', `translate(${width - 250}, 15)`);
    
    legend.append('rect')
      .attr('x', -10)
      .attr('y', -10)
      .attr('width', 240)
      .attr('height', legendData.length * 30 + 20)
      .attr('rx', 6)
      .attr('fill', 'rgba(255, 255, 255, 0.95)')
      .attr('stroke', '#bdc3c7')
      .attr('stroke-width', 2);
    
    legendData.forEach((item, idx) => {
      const legendItem = legend.append('g')
        .attr('transform', `translate(5, ${idx * 30 + 5})`)
        .attr('opacity', 0);
      
      legendItem.append('circle')
        .attr('r', 9)
        .attr('fill', item.color)
        .attr('stroke', '#2c3e50')
        .attr('stroke-width', 1.5);
      
      legendItem.append('text')
        .attr('x', 18)
        .attr('y', 0)
        .attr('font-size', '13px')
        .attr('dominant-baseline', 'middle')
        .text(item.icon);
      
      legendItem.append('text')
        .attr('x', 40)
        .attr('y', 0)
        .attr('font-size', '13px')
        .attr('font-weight', '500')
        .attr('dominant-baseline', 'middle')
        .attr('fill', '#2c3e50')
        .text(item.label);
      
      // Apply transition after elements are added
      legendItem
        .transition()
        .delay(1200 + idx * 100)
        .duration(400)
        .attr('opacity', 1);
    });

    // Create tooltip for node details
    const nodeTooltip = d3.select('body').append('div')
      .attr('class', 'node-tooltip')
      .style('position', 'absolute')
      .style('visibility', 'hidden')
      .style('background-color', 'rgba(0, 0, 0, 0.9)')
      .style('color', 'white')
      .style('padding', '12px 16px')
      .style('border-radius', '8px')
      .style('font-size', '13px')
      .style('pointer-events', 'none')
      .style('z-index', '1000')
      .style('max-width', '300px')
      .style('box-shadow', '0 4px 12px rgba(0,0,0,0.3)');

    // Draw nodes with animations
    nodes.forEach((node, idx) => {
      const g = svg.append('g')
        .attr('transform', `translate(${node.x},${node.y})`)
        .attr('opacity', 0);

      // Add pulsing glow effect for highlighted nodes
      if (node.highlighted) {
        const glowCircle = g.append('circle')
          .attr('r', (node.size || nodeRadius) + 10)
          .attr('fill', 'none')
          .attr('stroke', node.color)
          .attr('stroke-width', 4)
          .attr('opacity', 0.6);
        
        // Pulsing animation
        const pulse = (): void => {
          glowCircle
            .transition()
            .duration(1500)
            .attr('r', (node.size || nodeRadius) + 18)
            .attr('opacity', 0.1)
            .transition()
            .duration(1500)
            .attr('r', (node.size || nodeRadius) + 10)
            .attr('opacity', 0.6)
            .on('end', pulse);
        };
        pulse();
      }

      // Main circle with shadow
      g.append('circle')
        .attr('r', node.size || nodeRadius)
        .attr('fill', node.color)
        .attr('stroke', node.highlighted ? '#f39c12' : '#2c3e50')
        .attr('stroke-width', node.highlighted ? 5 : 3)
        .attr('filter', 'drop-shadow(0 6px 10px rgba(0,0,0,0.4))')
        .style('cursor', 'pointer')
        .on('mouseenter', function(event) {
          d3.select(this)
            .transition()
            .duration(200)
            .attr('r', (node.size || nodeRadius) + 5);
          
          // Show detailed tooltip
          let tooltipContent = `<strong style="font-size: 14px; color: #f39c12;">${node.icon} ${node.label.split('\\n')[0]}</strong><br/>`;
          
          if (node.id === 'user') {
            tooltipContent += `<br/><span style="color: #95a5a6;">Role:</span> Traffic Source<br/><span style="color: #95a5a6;">Type:</span> User Device/System`;
          } else if (node.id === 'guard') {
            tooltipContent += `<br/><span style="color: #95a5a6;">Role:</span> Entry Guard Node<br/>`;
            if (entryNode) {
              tooltipContent += `<span style="color: #95a5a6;">Fingerprint:</span> ${entryNode}<br/>`;
              if (entryCountry) {
                tooltipContent += `<span style="color: #95a5a6;">Location:</span> ${entryCountry}`;
                if (entryCountryName) {
                  tooltipContent += ` (${entryCountryName})`;
                }
                tooltipContent += `<br/>`;
              }
              tooltipContent += `<span style="color: #95a5a6;">Status:</span> <span style="color: #2ecc71;">✓ Identified</span>`;
            } else {
              tooltipContent += `<span style="color: #95a5a6;">Status:</span> <span style="color: #e74c3c;">Not Yet Identified</span>`;
            }
          } else if (node.id === 'middle') {
            tooltipContent += `<br/><span style="color: #95a5a6;">Role:</span> Middle Relay<br/><span style="color: #95a5a6;">Type:</span> Intermediate Node<br/><span style="color: #95a5a6;">Function:</span> Forwards encrypted traffic`;
          } else if (node.id === 'exit') {
            tooltipContent += `<br/><span style="color: #95a5a6;">Role:</span> Exit Node<br/>`;
            if (exitNode) {
              tooltipContent += `<span style="color: #95a5a6;">Fingerprint:</span> ${exitNode}<br/>`;
              tooltipContent += `<span style="color: #95a5a6;">Status:</span> <span style="color: #2ecc71;">✓ Identified</span>`;
            } else {
              tooltipContent += `<span style="color: #95a5a6;">Status:</span> <span style="color: #e74c3c;">Not Yet Identified</span>`;
            }
          }
          
          nodeTooltip
            .style('visibility', 'visible')
            .html(tooltipContent);
        })
        .on('mousemove', function(event) {
          nodeTooltip
            .style('top', (event.pageY - 10) + 'px')
            .style('left', (event.pageX + 15) + 'px');
        })
        .on('mouseleave', function() {
          d3.select(this)
            .transition()
            .duration(200)
            .attr('r', node.size || nodeRadius);
          
          nodeTooltip.style('visibility', 'hidden');
        });

      // Add icon
      g.append('text')
        .attr('text-anchor', 'middle')
        .attr('dominant-baseline', 'middle')
        .attr('font-size', '34px')
        .attr('y', -8)
        .style('pointer-events', 'none')
        .text(node.icon);

      // Add label with better formatting
      const labelLines = node.label.split('\n');
      labelLines.forEach((line, lineIdx) => {
        g.append('text')
          .attr('text-anchor', 'middle')
          .attr('dominant-baseline', 'middle')
          .attr('y', (node.size || nodeRadius) + 28 + (lineIdx * 16))
          .attr('font-size', lineIdx === 0 ? '15px' : '13px')
          .attr('font-weight', lineIdx === 0 ? 'bold' : '600')
          .attr('fill', '#2c3e50')
          .style('pointer-events', 'none')
          .text(line);
      });

      // Animate node appearance
      g.transition()
        .delay(idx * 150)
        .duration(500)
        .attr('opacity', 1);
    });

    // Add title
    svg.append('text')
      .attr('x', width / 2)
      .attr('y', 25)
      .attr('text-anchor', 'middle')
      .attr('font-size', '16px')
      .attr('font-weight', 'bold')
      .attr('fill', '#2c3e50')
      .text('TOR Network Path Visualization');

  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [entryNode, exitNode]);

  return (
    <div className="path-diagram-container">
      <svg ref={svgRef}></svg>
      <div className="path-legend">
        <p>
          <strong>How TOR Works:</strong> Traffic passes through three encrypted layers - 
          Guard → Middle → Exit - each only knowing their immediate predecessor and successor.
        </p>
      </div>
    </div>
  );
};

export default PathDiagram;
