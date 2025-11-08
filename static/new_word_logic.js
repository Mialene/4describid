document.addEventListener("DOMContentLoaded", function(){
    const submitBtn = document.querySelector('button[value="submit"]');
    const display = document.getElementById("display");

    // Function to check if submit should be enabled
    function updateSubmitButton() {
        const keyword = display.innerHTML.trim();
        if (keyword === "" || keyword === "Error generating keyword") {
            submitBtn.disabled = true;
            submitBtn.classList.add('disabled');
        } else {
            submitBtn.disabled = false;
            submitBtn.classList.remove('disabled');
        }
    }
    
    // Check on page load
    updateSubmitButton();

    document.getElementById("generate-word").addEventListener("click", function(event){
        event.preventDefault(); // Prevent the default form submission

        // Disable both buttons
        const generateBtn = document.getElementById("generate-word");
        const submitBtn = document.querySelector('button[name="action"][value="submit"]');
        
        generateBtn.disabled = true;
        submitBtn.disabled = true;
        
        // Add loading state (optional: change button text/style)
        const originalText = generateBtn.textContent;
        generateBtn.textContent = "Generating...";
        generateBtn.style.cursor = "wait";
        document.body.style.cursor = "wait"; // Make whole page cursor spin
    
        
        fetch("/new_describid", { 
            method: "POST",
            headers: {
                "Content-Type": "application/x-www-form-urlencoded",
            },
            body: 'action=generate' // Send the action parameter
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        }) 
        .then(data => {
            if(data.success){
                playRandomAnimation()
                document.getElementById("display").innerHTML = data.keyword
                updateSubmitButton(); // Enable submit after keyword is set
            } else {
                console.error('Server returned success: false');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            document.getElementById("display").innerHTML = 'Error generating keyword';
            updateSubmitButton(); // Keep disabled on error
        })
        .finally(() => {
        // Re-enable buttons and restore cursor
        generateBtn.disabled = false;
        submitBtn.disabled = false;
        generateBtn.textContent = originalText;
        generateBtn.style.cursor = "";
        document.body.style.cursor = "";
        });
    });

    function playRandomAnimation() {
        document.getElementById("display") //
    }
});