console.log('adminindex.js loaded successfully!');

<script src="/static/js/adminindex.js"></script>

    // ============================
    // 🎯 Pie Chart for Sales Overview
    // ============================
    var ctxPie = document.getElementById('salesPieChart').getContext('2d');
    var salesPieChart = new Chart(ctxPie, {
        type: 'pie', // Pie chart
        data: {
            labels: ['Online', 'In-Store', 'Wholesale'], // Labels
            datasets: [{
                label: 'Sales Distribution',
                data: [50, 30, 20], // Data points for pie chart
                backgroundColor: ['#4caf50', '#ff9800', '#03a9f4'],
                hoverOffset: 4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false
        }
    });

    // ============================
    // 📊 Bar Chart for Monthly Sales
    // ============================
    var ctxBar = document.getElementById('monthlySalesChart').getContext('2d');
    var monthlySalesChart = new Chart(ctxBar, {
        type: 'bar',
        data: {
            labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
            datasets: [{
                label: 'Sales ($)',
                data: [1200, 1900, 3000, 2500, 3200, 2700],
                backgroundColor: '#4caf50',
                borderColor: '#388e3c',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });

 