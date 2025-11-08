document.addEventListener('DOMContentLoaded', function() {
    // Add event listeners or any other JavaScript code here
    document.querySelectorAll('.play-card').forEach(card => {
        card.addEventListener('click', function() {
            // redirect to the play page
            const playId = this.querySelector('#play-id').textContent.split(': ')[1];
            window.location.href = `/play/${playId}`;
        });
    });
    
    // explore: change tabs
    const lastTab = sessionStorage.getItem('exploreTab') || 'forbid';
    if (lastTab === 'guess') {
        document.getElementById('guess-rbtn').checked = true;
        document.getElementById('guess-panel').classList.add('active');
        document.getElementById('forbid-panel').classList.remove('active');
        document.getElementById('explore-header').textContent = 'Guess Plays';
    } else {
        document.getElementById('forbid-rbtn').checked = true;
        document.getElementById('forbid-panel').classList.add('active');
        document.getElementById('guess-panel').classList.remove('active');
        document.getElementById('explore-header').textContent = 'Forbid Plays';
    }
    
    // Save tab state when switching tabs
    document.getElementById('forbid-rbtn').addEventListener('change', function() {
        if (this.checked) {
            sessionStorage.setItem('exploreTab', 'forbid');
            document.getElementById('forbid-panel').classList.add('active');
            document.getElementById('guess-panel').classList.remove('active');
            document.getElementById('explore-header').textContent = 'Forbid Plays';
        }
    }); // This closing parenthesis and brace were missing
    
    document.getElementById('guess-rbtn').addEventListener('change', function() {
        if (this.checked) {
            sessionStorage.setItem('exploreTab', 'guess');
            document.getElementById('guess-panel').classList.add('active');
            document.getElementById('forbid-panel').classList.remove('active');
            document.getElementById('explore-header').textContent = 'Guess Plays';
        }
    });

    // History: change tabs
    const lastHistTab = sessionStorage.getItem('historyTab') || 'me-played';
    if (lastTab === 'all-played') {
        document.getElementById('all-played-rbtn').checked = true;
        document.getElementById('all-played-panel').classList.add('active');
        document.getElementById('me-played-panel').classList.remove('active');
        document.getElementById('history-header').textContent = 'All history';
    } else {
        document.getElementById('me-played-rbtn').checked = true;
        document.getElementById('me-played-panel').classList.add('active');
        document.getElementById('all-played-panel').classList.remove('active');
        document.getElementById('history-header').textContent = 'Past plays I participated in';
    }
    
    // Save tab state when switching tabs
    document.getElementById('me-played-rbtn').addEventListener('change', function() {
        if (this.checked) {
            sessionStorage.setItem('historyTab', 'me-played');
            document.getElementById('me-played-panel').classList.add('active');
            document.getElementById('all-played-panel').classList.remove('active');
            document.getElementById('history-header').textContent = 'Past plays I participated in';
        }
    }); // This closing parenthesis and brace were missing
    
    document.getElementById('all-played-rbtn').addEventListener('change', function() {
        if (this.checked) {
            sessionStorage.setItem('historyTab', 'all-played');
            document.getElementById('all-played-panel').classList.add('active');
            document.getElementById('me-played-panel').classList.remove('active');
            document.getElementById('history-header').textContent = 'All history';
        }
    });
});