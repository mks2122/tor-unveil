import React, { useEffect, useRef, useState } from 'react';
import * as d3 from 'd3';

interface TimelineEvent {
  id: number;
  event_type: string;
  timestamp: string;
  node_fingerprint?: string;
  event_metadata?: any;
}

interface TimelineViewProps {
  analysisId: number | null;
}

const TimelineView: React.FC<TimelineViewProps> = ({ analysisId }) => {
  const svgRef = useRef<SVGSVGElement>(null);
  const [events, setEvents] = useState<TimelineEvent[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!analysisId) {
      console.log('TimelineView: No analysisId provided');
      return;
    }

    console.log('TimelineView: Fetching timeline for analysis ID:', analysisId);

    const fetchTimeline = async () => {
      setLoading(true);
      try {
        const response = await fetch(`http://localhost:8000/api/analysis/timeline/${analysisId}`);
        console.log('TimelineView: Response status:', response.status);
        
        if (response.ok) {
          const data = await response.json();
          console.log('TimelineView: Received data:', data);
          console.log('TimelineView: Events count:', data.events?.length || 0);
          setEvents(data.events || []);
        } else {
          console.error('TimelineView: Failed to fetch timeline:', response.statusText);
        }
      } catch (error) {
        console.error('TimelineView: Error fetching timeline:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchTimeline();
  }, [analysisId]);

  useEffect(() => {
    if (events.length === 0 || !svgRef.current) return;

    // Clear previous SVG
    d3.select(svgRef.current).selectAll('*').remove();

    const margin = { top: 40, right: 20, bottom: 60, left: 100 };
    const width = 900 - margin.left - margin.right;
    const height = 400 - margin.top - margin.bottom;

    const svg = d3.select(svgRef.current)
      .attr('width', width + margin.left + margin.right)
      .attr('height', height + margin.top + margin.bottom)
      .append('g')
      .attr('transform', `translate(${margin.left},${margin.top})`);

    // Parse timestamps
    const timeExtent = d3.extent(events, d => new Date(d.timestamp)) as [Date, Date];
    
    // Create scales
    const xScale = d3.scaleTime()
      .domain(timeExtent)
      .range([0, width]);

    const eventTypes = Array.from(new Set(events.map(e => e.event_type)));
    const yScale = d3.scaleBand()
      .domain(eventTypes)
      .range([0, height])
      .padding(0.3);

    // Color scale with more colors for different event types
    const colorScale = d3.scaleOrdinal<string>()
      .domain(eventTypes)
      .range(['#3498db', '#2ecc71', '#e74c3c', '#f39c12', '#9b59b6', '#1abc9c', '#e67e22', '#16a085', '#8e44ad', '#c0392b']);

    // Add axes
    svg.append('g')
      .attr('transform', `translate(0,${height})`)
      .call(d3.axisBottom(xScale).ticks(6))
      .selectAll('text')
      .style('font-size', '12px');

    svg.append('g')
      .call(d3.axisLeft(yScale))
      .selectAll('text')
      .style('font-size', '12px')
      .style('font-weight', '500');

    // Add grid lines
    svg.append('g')
      .attr('class', 'grid')
      .attr('opacity', 0.1)
      .call(d3.axisBottom(xScale)
        .ticks(6)
        .tickSize(height)
        .tickFormat(() => '')
      );

    // Tooltip
    const tooltip = d3.select('body').append('div')
      .attr('class', 'timeline-tooltip')
      .style('position', 'absolute')
      .style('visibility', 'hidden')
      .style('background-color', 'rgba(0, 0, 0, 0.8)')
      .style('color', 'white')
      .style('padding', '10px')
      .style('border-radius', '5px')
      .style('font-size', '12px')
      .style('pointer-events', 'none')
      .style('z-index', '1000');

    // Add events as circles
    svg.selectAll('circle')
      .data(events)
      .enter()
      .append('circle')
      .attr('cx', d => xScale(new Date(d.timestamp)))
      .attr('cy', d => (yScale(d.event_type) || 0) + (yScale.bandwidth() / 2))
      .attr('r', 0)
      .attr('fill', d => colorScale(d.event_type))
      .attr('opacity', 0.8)
      .attr('stroke', 'white')
      .attr('stroke-width', 2)
      .on('mouseover', function(event, d) {
        d3.select(this)
          .transition()
          .duration(200)
          .attr('r', 10)
          .attr('opacity', 1);
        
        // Build detailed tooltip based on event type
        let tooltipHTML = `<div style="min-width: 250px;">
          <strong style="font-size: 14px; color: #f39c12;">${d.event_type.replace(/_/g, ' ').toUpperCase()}</strong><br/>
          <span style="color: #95a5a6;">Time:</span> ${new Date(d.timestamp).toLocaleString()}<br/>`
        
        if (d.node_fingerprint) {
          tooltipHTML += `<span style="color: #95a5a6;">Node:</span> ${d.node_fingerprint}<br/>`;
        }
        
        // Add metadata if available
        if (d.event_metadata) {
          const meta = d.event_metadata;
          if (meta.confidence) {
            tooltipHTML += `<span style="color: #95a5a6;">Confidence:</span> ${(meta.confidence * 100).toFixed(1)}%<br/>`;
          }
          if (meta.country) {
            tooltipHTML += `<span style="color: #95a5a6;">Country:</span> ${meta.country}<br/>`;
          }
          if (meta.simulation_count) {
            tooltipHTML += `<span style="color: #95a5a6;">Simulations:</span> ${meta.simulation_count}<br/>`;
          }
          if (meta.simulation_num) {
            tooltipHTML += `<span style="color: #95a5a6;">Simulation #:</span> ${meta.simulation_num}<br/>`;
          }
          if (meta.correlation_score) {
            tooltipHTML += `<span style="color: #95a5a6;">Correlation:</span> ${(meta.correlation_score * 100).toFixed(1)}%<br/>`;
          }
          if (meta.guard_count) {
            tooltipHTML += `<span style="color: #95a5a6;">Guards:</span> ${meta.guard_count}<br/>`;
          }
          if (meta.execution_time) {
            tooltipHTML += `<span style="color: #95a5a6;">Duration:</span> ${meta.execution_time.toFixed(2)}s<br/>`;
          }
          if (meta.guards_analyzed) {
            tooltipHTML += `<span style="color: #95a5a6;">Analyzed:</span> ${meta.guards_analyzed} nodes<br/>`;
          }
        }
        
        tooltipHTML += '</div>';
        
        tooltip
          .style('visibility', 'visible')
          .html(tooltipHTML);
      })
      .on('mousemove', function(event) {
        tooltip
          .style('top', (event.pageY - 60) + 'px')
          .style('left', (event.pageX + 10) + 'px');
      })
      .on('mouseout', function() {
        d3.select(this)
          .transition()
          .duration(200)
          .attr('r', 6)
          .attr('opacity', 0.8);
        
        tooltip.style('visibility', 'hidden');
      })
      .transition()
      .duration(800)
      .attr('r', 6);

    // Add title
    svg.append('text')
      .attr('x', width / 2)
      .attr('y', -20)
      .attr('text-anchor', 'middle')
      .style('font-size', '16px')
      .style('font-weight', 'bold')
      .text('Analysis Timeline');

    // Cleanup
    return () => {
      tooltip.remove();
    };
  }, [events]);

  if (loading) {
    return <div className="timeline-loading">Loading timeline...</div>;
  }

  if (events.length === 0) {
    return <div className="timeline-empty">No timeline events available</div>;
  }

  return (
    <div className="timeline-container">
      <svg ref={svgRef}></svg>
      <div className="timeline-legend">
        <h4>Event Details</h4>
        <table>
          <thead>
            <tr>
              <th>Time</th>
              <th>Event Type</th>
              <th>Details</th>
            </tr>
          </thead>
          <tbody>
            {events.slice(0, 10).map(event => (
              <tr key={event.id}>
                <td>{new Date(event.timestamp).toLocaleTimeString()}</td>
                <td>{event.event_type}</td>
                <td>{event.node_fingerprint?.substring(0, 20) || 'N/A'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default TimelineView;
