// app.js
document.addEventListener('DOMContentLoaded', function() {
    // Player search with autocomplete
    const playerSearch = document.getElementById('playerSearch');
    const playerResults = document.getElementById('playerResults');
    const searchForm = document.getElementById('searchForm');

    // View toggle buttons
    const viewTable = document.getElementById('viewTable');
    const viewGraph = document.getElementById('viewGraph');
    const tableView = document.getElementById('table-view');
    const graphView = document.getElementById('graph-view');

    // Initialize Force Directed Graph
    let simulation;
    let svg;

    // Hard-coded ESPN IDs for Bo Nix's connections
    const boNixConnectionIds = {
        "Trey Lindsey": "4587295",
        "Sawyer Pate": "4689081",
        "Tez Johnson": "4608810",
        "Wil Appleton": "4283012",
        "TJ Finley": "4431948",
        "Chayil Garnett": "4432157",
        "Jay Butterfield": "4430865",
        "Dematrius Davis Jr.": "4432690",
        "Ty Thompson": "4432774",
        "Grant Loy": "4046743",
        "Bo Nix": "4426338"
    };

    // Helper function to format connection types
    function formatConnectionType(type) {
        // Replace underscores with spaces
        let formatted = type.replace(/_/g, ' ');

        // Handle specific connection types
        switch(type) {
            case 'TEAMMATE_WITH':
                return 'Teammate';
            case 'SAME_POSITION_GROUP':
                return 'Same Position';
            case 'SAME_STATE_TEAM':
                return 'Same State';
            case 'SAME_UNIT':
                return 'Same Unit';
            case 'SAME_HOMETOWN':
                return 'Same Hometown';
            default:
                // Format other types by capitalizing first letter of each word
                return formatted.split(' ')
                    .map(word => word.charAt(0) + word.slice(1).toLowerCase())
                    .join(' ');
        }
    }

    // Function to generate an ESPN profile URL, using hard-coded IDs when available
    function generateEspnProfileUrl(firstName, lastName) {
        if (!firstName || !lastName) return '#';

        const fullName = `${firstName} ${lastName}`;

        // Check if this is one of Bo Nix's connections with a hard-coded ID
        if (boNixConnectionIds[fullName]) {
            const espnName = `${firstName.toLowerCase()}-${lastName.toLowerCase()}`.replace(/\s+/g, '-');
            return `https://www.espn.com/college-football/player/_/id/${boNixConnectionIds[fullName]}/${espnName}`;
        }

        // If not in our lookup table, fall back to the original method
        const espnName = `${firstName.toLowerCase()}-${lastName.toLowerCase()}`;
        const mockId = Math.abs(hashCode(`${firstName}${lastName}`)) % 10000000;
        return `https://www.espn.com/college-football/player/_/id/${mockId}/${espnName}`;
    }

    // Simple string hash function
    function hashCode(str) {
        let hash = 0;
        for (let i = 0; i < str.length; i++) {
            const char = str.charCodeAt(i);
            hash = ((hash << 5) - hash) + char;
            hash = hash & hash; // Convert to 32bit integer
        }
        return hash;
    }

    // Player search autocomplete
    playerSearch.addEventListener('input', function() {
        const name = playerSearch.value.trim();
        if (name.length < 2) {
            playerResults.innerHTML = '';
            return;
        }

        fetch(`/search_players?name=${encodeURIComponent(name)}`)
            .then(response => response.json())
            .then(data => {
                playerResults.innerHTML = '';
                if (data.length === 0) {
                    playerResults.innerHTML = '<div class="alert alert-info">No players found</div>';
                    return;
                }

                const list = document.createElement('div');
                list.className = 'list-group';

                data.forEach(player => {
                    // Use the correct property names from your Neo4j query
                    const firstName = player.first_name || player["p.first_name"];
                    const lastName = player.last_name || player["p.last_name"];

                    const item = document.createElement('button');
                    item.type = 'button';
                    item.className = 'list-group-item list-group-item-action';
                    item.textContent = `${firstName} ${lastName}`;
                    item.addEventListener('click', function() {
                        playerSearch.value = `${firstName} ${lastName}`;
                        playerResults.innerHTML = '';
                    });
                    list.appendChild(item);
                });

                playerResults.appendChild(list);
            })
            .catch(error => console.error('Error searching players:', error));
    });

    // Form submission to get player connections
    searchForm.addEventListener('submit', function(e) {
        e.preventDefault();
        const playerName = playerSearch.value.trim();
        if (!playerName) return;

        // Show loading state
        document.getElementById('network-visualization').innerHTML = '<div class="d-flex justify-content-center align-items-center h-100"><div class="spinner-border text-primary" role="status"><span class="visually-hidden">Loading...</span></div></div>';

        fetch('/get_player_connections', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: `name=${encodeURIComponent(playerName)}`
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                document.getElementById('network-visualization').innerHTML = `<div class="alert alert-danger">${data.error}</div>`;
                return;
            }

            // Update player network title with link
            const playerNameParts = data.player.split(' ');
            const playerFirstName = playerNameParts[0];
            const playerLastName = playerNameParts.slice(1).join(' ');
            const playerUrl = data.player_url || generateEspnProfileUrl(playerFirstName, playerLastName);

            document.getElementById('playerNetworkTitle').innerHTML = `
                <a href="${playerUrl}" target="_blank" class="player-link">${data.player}</a>'s Network
            `;

            // Update connection stats
            updateConnectionStats(data);

            // Update table view
            updateTableView(data.top_connections);

            // Update network visualization
            createNetworkGraph(data);
        })
        .catch(error => {
            console.error('Error fetching connections:', error);
            document.getElementById('network-visualization').innerHTML = '<div class="alert alert-danger">Error loading player connections</div>';
        });
    });

    // Toggle between table and graph views
    if (viewTable && viewGraph) {
        viewTable.addEventListener('click', function() {
            tableView.style.display = 'block';
            graphView.style.display = 'none';
            viewTable.classList.add('active');
            viewGraph.classList.remove('active');
        });

        viewGraph.addEventListener('click', function() {
            tableView.style.display = 'none';
            graphView.style.display = 'block';
            viewGraph.classList.add('active');
            viewTable.classList.remove('active');
        });
    }

    // Function to update connection stats
    function updateConnectionStats(data) {
        const statsDiv = document.getElementById('connectionStats');
        if (!statsDiv) return;

        // Calculate some stats
        const totalConnections = data.top_connections.length;
        const connectionStrengths = data.top_connections.map(c => c.connection_strength);
        const averageStrength = connectionStrengths.length ?
            (connectionStrengths.reduce((a, b) => a + b, 0) / connectionStrengths.length).toFixed(1) : 0;

        // Count connection types with readable formatting
        const allTypes = data.top_connections.flatMap(c => c.connection_types);
        const typeCount = {};
        allTypes.forEach(type => {
            typeCount[type] = (typeCount[type] || 0) + 1;
        });

        // Create HTML
        statsDiv.innerHTML = `
            <div class="mb-3">
                <div class="fw-bold fs-4 text-primary">${totalConnections}</div>
                <div class="text-muted">Strong Connections</div>
            </div>
            <div class="mb-3">
                <div class="fw-bold fs-4 text-success">${averageStrength}</div>
                <div class="text-muted">Avg. Connection Strength</div>
            </div>
            <div>
                <h6>Connection Types:</h6>
                <ul class="list-unstyled">
                    ${Object.entries(typeCount).map(([type, count]) => 
                        `<li><span class="badge bg-secondary">${count}</span> ${formatConnectionType(type)}</li>`
                    ).join('')}
                </ul>
            </div>
        `;
    }

    // Function to update table view
    function updateTableView(connections) {
        const tableBody = document.getElementById('connections-table');
        if (!tableBody) return;

        tableBody.innerHTML = '';

        connections.forEach(conn => {
            // Get property names correctly - check both possible naming conventions
            const firstName = conn.teammate_first_name || conn["teammate.first_name"];
            const lastName = conn.teammate_last_name || conn["teammate.last_name"];
            const connectionStrength = conn.connection_strength;
            const connectionTypes = conn.connection_types;

            // Get profile URL using the hard-coded IDs if available
            const profileUrl = conn.profile_url || generateEspnProfileUrl(firstName, lastName);

            // Format connection types to be more readable
            const formattedTypes = connectionTypes.map(formatConnectionType);

            // Calculate a "warm lead score" based on connection strength and types
            const warmLeadScore = conn.warm_lead_score || connectionStrength;

            const row = document.createElement('tr');
            row.innerHTML = `
                <td>
                    <a href="${profileUrl}" target="_blank" class="player-link">
                        ${firstName || 'Unknown'} ${lastName || 'Unknown'}
                    </a>
                </td>
                <td>${connectionStrength}</td>
                <td>
                    ${formattedTypes.map(type => 
                        `<span class="badge bg-info text-dark me-1">${type}</span>`
                    ).join(' ')}
                </td>
                <td><span class="badge bg-${warmLeadScore > 10 ? 'success' : warmLeadScore > 5 ? 'warning' : 'secondary'}">${warmLeadScore}</span></td>
            `;
            tableBody.appendChild(row);
        });
    }

    // Function to create network graph visualization
    function createNetworkGraph(data) {
        const container = document.getElementById('network-visualization');
        if (!container) return;

        container.innerHTML = '';

        // Set up SVG
        svg = d3.select('#network-visualization')
            .append('svg')
            .attr('width', '100%')
            .attr('height', '100%')
            .attr('viewBox', '0 0 900 500');

        // Create nodes data
        const nodes = [];
        // Center node is the main player
        const mainPlayerName = data.player.split(' ');
        const mainPlayerFirstName = mainPlayerName[0];
        const mainPlayerLastName = mainPlayerName.slice(1).join(' ');

        nodes.push({
            id: 'center',
            name: data.player,
            firstName: mainPlayerFirstName,
            lastName: mainPlayerLastName,
            group: 0,
            url: data.player_url || generateEspnProfileUrl(mainPlayerFirstName, mainPlayerLastName)
        });

        // Add connection nodes
        data.top_connections.forEach((conn, i) => {
            // Use the correct property names
            const firstName = conn.teammate_first_name || conn["teammate.first_name"];
            const lastName = conn.teammate_last_name || conn["teammate.last_name"];

            // Get profile URL using hard-coded IDs if available
            const profileUrl = conn.profile_url || generateEspnProfileUrl(firstName, lastName);

            // Format connection types for tooltip
            const formattedTypes = conn.connection_types.map(formatConnectionType).join(', ');

            nodes.push({
                id: `conn-${i}`,
                name: `${firstName} ${lastName}`,
                firstName: firstName,
                lastName: lastName,
                group: 1,
                strength: conn.connection_strength,
                types: formattedTypes,
                url: profileUrl
            });
        });

        // Create links data
        const links = data.top_connections.map((conn, i) => ({
            source: 'center',
            target: `conn-${i}`,
            value: conn.connection_strength
        }));

        // Create force simulation
        simulation = d3.forceSimulation(nodes)
            .force('link', d3.forceLink(links).id(d => d.id).distance(d => 150 - d.value * 5))
            .force('charge', d3.forceManyBody().strength(-400))
            .force('center', d3.forceCenter(450, 250));

        // Create links
        const link = svg.append('g')
            .attr('class', 'links')
            .selectAll('line')
            .data(links)
            .enter().append('line')
            .attr('stroke-width', d => Math.sqrt(d.value))
            .attr('stroke', '#999')
            .attr('stroke-opacity', 0.6);

        // Create nodes
        const node = svg.append('g')
            .attr('class', 'nodes')
            .selectAll('g')
            .data(nodes)
            .enter().append('g')
            .attr('cursor', 'pointer')
            .on('click', (event, d) => {
                // Open ESPN profile in new tab when node is clicked
                window.open(d.url, '_blank');
            });

        // Create circles for nodes
        node.append('circle')
            .attr('r', d => d.group === 0 ? 25 : 15 + (d.strength ? Math.sqrt(d.strength) : 0))
            .attr('fill', d => d.group === 0 ? '#3182bd' : '#e6550d');

        // Add labels to nodes
        node.append('text')
            .attr('dy', d => d.group === 0 ? 35 : 25)
            .attr('text-anchor', 'middle')
            .text(d => d.name)
            .style('font-size', '12px')
            .style('fill', '#333')
            .style('font-weight', d => d.group === 0 ? 'bold' : 'normal');

        // Add hover tooltip
        node.append('title')
            .text(d => {
                if (d.group === 0) {
                    return `${d.name}\nClick to view ESPN profile`;
                } else {
                    return `${d.name}\nStrength: ${d.strength}\nTypes: ${d.types}\nClick to view ESPN profile`;
                }
            });

        // Add drag capability
        node.call(d3.drag()
            .on('start', dragstarted)
            .on('drag', dragged)
            .on('end', dragended));

        // Update positions on each tick
        simulation.on('tick', () => {
            link
                .attr('x1', d => d.source.x)
                .attr('y1', d => d.source.y)
                .attr('x2', d => d.target.x)
                .attr('y2', d => d.target.y);

            node.attr('transform', d => `translate(${d.x},${d.y})`);
        });

        // Drag functions
        function dragstarted(event) {
            if (!event.active) simulation.alphaTarget(0.3).restart();
            event.subject.fx = event.subject.x;
            event.subject.fy = event.subject.y;
        }

        function dragged(event) {
            event.subject.fx = event.x;
            event.subject.fy = event.y;
        }

        function dragended(event) {
            if (!event.active) simulation.alphaTarget(0);
            event.subject.fx = null;
            event.subject.fy = null;
        }
    }
});