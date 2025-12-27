// File detail page functionality

// Highlight specific line in code viewer
function highlightLine(lineNumber) {
    // Remove existing highlights
    document.querySelectorAll('.line-number').forEach(el => {
        el.style.backgroundColor = '';
        el.style.color = '';
    });
    
    // Highlight the target line
    const lineElements = document.querySelectorAll('.line-number');
    lineElements.forEach(el => {
        if (el.getAttribute('data-line') == lineNumber) {
            el.style.backgroundColor = '#fbbf24';
            el.style.color = '#000';
            el.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
    });
}

// Filter issues by severity
document.addEventListener('DOMContentLoaded', function() {
    const filterButtons = document.querySelectorAll('.filter-btn');
    const issueCards = document.querySelectorAll('.issue-card');
    
    filterButtons.forEach(button => {
        button.addEventListener('click', function() {
            // Update active button
            filterButtons.forEach(btn => btn.classList.remove('active'));
            this.classList.add('active');
            
            const filter = this.getAttribute('data-filter');
            
            // Filter issues
            issueCards.forEach(card => {
                if (filter === 'all') {
                    card.style.display = 'block';
                } else {
                    const severity = card.getAttribute('data-severity');
                    card.style.display = severity === filter ? 'block' : 'none';
                }
            });
        });
    });
});

// Update issue status
async function updateIssueStatus(issueId, newStatus) {
    try {
        const response = await fetch(`/api/issue/${issueId}/status`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ status: newStatus })
        });
        
        const result = await response.json();
        
        if (response.ok && result.success) {
            // Find the issue card and update its appearance
            const issueCard = document.querySelector(`.issue-card [data-issue-id="${issueId}"]`)?.closest('.issue-card');
            if (issueCard) {
                if (newStatus === 'resolved') {
                    issueCard.style.opacity = '0.5';
                    issueCard.style.textDecoration = 'line-through';
                } else if (newStatus === 'ignored') {
                    issueCard.style.display = 'none';
                }
            }
            
            alert(`Issue marked as ${newStatus}`);
        } else {
            alert('Error updating issue status');
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Failed to update issue status');
    }
}

// Apply AI-generated fix to code
async function applyFix(issueId) {
    if (!confirm('Apply this fix to your code? This will modify the file.')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/issue/${issueId}/apply-fix`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        const data = await response.json();
        
        if (response.ok) {
            alert(data.message || 'Fix applied successfully!');
            location.reload();
        } else {
            alert(data.error || 'Failed to apply fix');
        }
    } catch (error) {
        console.error('Error:', error);
        alert('An error occurred while applying fix');
    }
}

// Auto-fix all fixable issues
async function autoFixAll() {
    const fileId = window.location.pathname.split('/').pop();
    
    if (!confirm('Apply all available fixes? This will modify the file with all AI-suggested fixes.')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/file/${fileId}/auto-fix-all`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        const data = await response.json();
        
        if (response.ok) {
            alert(data.message || `Applied ${data.fixed_count} fixes successfully!`);
            location.reload();
        } else {
            alert(data.error || 'Failed to apply fixes');
        }
    } catch (error) {
        console.error('Error:', error);
        alert('An error occurred while applying fixes');
    }
}
