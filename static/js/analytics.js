// Analytics page - Chart.js visualizations

document.addEventListener('DOMContentLoaded', function() {
    // Severity Distribution Chart
    const severityCtx = document.getElementById('severityChart');
    if (severityCtx && severityData) {
        new Chart(severityCtx, {
            type: 'doughnut',
            data: {
                labels: ['Critical', 'High', 'Medium', 'Low'],
                datasets: [{
                    label: 'Issues by Severity',
                    data: [
                        severityData.critical || 0,
                        severityData.high || 0,
                        severityData.medium || 0,
                        severityData.low || 0
                    ],
                    backgroundColor: [
                        '#ef4444',
                        '#f59e0b',
                        '#3b82f6',
                        '#10b981'
                    ],
                    borderWidth: 2,
                    borderColor: '#ffffff'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            padding: 15,
                            font: {
                                size: 12
                            }
                        }
                    }
                }
            }
        });
    }

    // Issue Type Chart
    const typeCtx = document.getElementById('typeChart');
    if (typeCtx && typeData) {
        const typeLabels = Object.keys(typeData);
        const typeValues = Object.values(typeData);
        
        new Chart(typeCtx, {
            type: 'bar',
            data: {
                labels: typeLabels.map(label => label.charAt(0).toUpperCase() + label.slice(1)),
                datasets: [{
                    label: 'Number of Issues',
                    data: typeValues,
                    backgroundColor: '#2563eb',
                    borderRadius: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            stepSize: 1
                        }
                    }
                }
            }
        });
    }

    // Project Issues Chart
    const projectCtx = document.getElementById('projectChart');
    if (projectCtx && projectsData) {
        const projectNames = projectsData.map(p => p.name);
        const projectIssueCounts = projectsData.map(p => {
            return p.files.reduce((total, file) => total + file.issues.length, 0);
        });
        
        new Chart(projectCtx, {
            type: 'line',
            data: {
                labels: projectNames,
                datasets: [{
                    label: 'Total Issues',
                    data: projectIssueCounts,
                    borderColor: '#2563eb',
                    backgroundColor: 'rgba(37, 99, 235, 0.1)',
                    tension: 0.4,
                    fill: true,
                    pointRadius: 5,
                    pointBackgroundColor: '#2563eb'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            stepSize: 1
                        }
                    }
                }
            }
        });
    }
});
