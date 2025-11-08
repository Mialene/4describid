document.addEventListener('DOMContentLoaded', function() {
    const modal = document.getElementById("forbidModal");
    const descriptionModal = document.getElementById("descriptionModal");
    
    // Debug: Check if elements exist
    console.log('forbidModal found:', modal);
    console.log('descriptionModal found:', descriptionModal);
    console.log('open-f-prompt button:', document.querySelector('.open-f-prompt'));
    console.log('open-d-prompt button:', document.querySelector('.open-d-prompt'));
    
    // Functions for opening modals
    const openForbidBtn = document.querySelector('.open-f-prompt');
    if (openForbidBtn) {
        openForbidBtn.addEventListener('click', () => {
            console.log('Opening forbid modal');
            if (modal) {
                modal.classList.add('open');
            }
        });
    }
    
    const openDescBtn = document.querySelector('.open-d-prompt');
    if (openDescBtn) {
        openDescBtn.addEventListener('click', () => {
            console.log('Opening description modal');
            if (descriptionModal) {
                descriptionModal.classList.add('open');
            }
        });
    }
    
    // Close on outside click - Forbid Modal
    if (modal) {
        modal.addEventListener('click', (event) => {
            console.log('Clicked on forbid modal', event.target);
            if (event.target === modal) {
                console.log('Closing forbid modal');
                modal.classList.remove("open");
            }
        });
    }
    
    // Close on outside click - Description Modal
    if (descriptionModal) {
        descriptionModal.addEventListener('click', (event) => {
            console.log('Clicked on description modal', event.target);
            if (event.target === descriptionModal) {
                console.log('Closing description modal');
                descriptionModal.classList.remove("open");
            }
        });
    }

    // const forbiddenWordsArray = (don't have to declare anymore)

    // logic to validate description
    document.getElementById("description").addEventListener("input", function() {
        const userText = this.value;

        const violatedIndices = getViolatedWords(userText, forbiddenWordsArray);
    
        if (violatedIndices.length > 0) {
            // Red border the violated word labels
            violatedIndices.forEach(index => {
                document.getElementById('label' + index).style.border = '2px solid red';
            });
            
            // Remove red border from non-violated labels
            for (let i = 0; i < forbiddenWordsArray.length; i++) {
                if (!violatedIndices.includes(i)) {
                    document.getElementById('label' + i).style.border = '';
                }
            }
        
        // Disable submit button
        document.querySelector('#descriptionModal .btn-outline-primary').disabled = true;
        } else {
            // Remove all red borders
            for (let i = 0; i < forbiddenWordsArray.length; i++) {
                document.getElementById('label' + i).style.border = '';
            }
            
            // Enable submit button
            document.querySelector('#descriptionModal .btn-outline-primary').disabled = false;
        }
    });

    function getViolatedWords(userText, forbiddenWordsArray) {
        const textNoSpaces = userText.replace(/\s+/g, '').toLowerCase();
        const violatedIndices = [];
        
        for (let i = 0; i < forbiddenWordsArray.length; i++) {
            const forbiddenNoSpaces = forbiddenWordsArray[i].replace(/\s+/g, '').toLowerCase();
            if (textNoSpaces.includes(forbiddenNoSpaces)) {
                violatedIndices.push(i); // Store the index
            }
        }
        
        return violatedIndices; // Returns array of indices, e.g., [0, 3, 5]
    }
});