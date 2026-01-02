// Backend URL - matches your ngrok URL
const BACKEND_URL = "https://rachitic-despairful-susannah.ngrok-free.dev";

// Google Sheet ID
const GOOGLE_SHEET_ID = "1llPlMFvsOfalvXNoOlUMeNW31yCEfAKpOH4Iwpu5B24";

console.log("🔗 Backend URL:", BACKEND_URL);
console.log("🌐 Current Page:", window.location.href);

// Read token from URL (for student page)
const params = new URLSearchParams(window.location.search);
const tokenFromURL = params.get("token");

let timerInterval;

// STUDENT: Mark attendance
async function markAttendance(event) {
  event.preventDefault();
  console.log("📝 Mark Attendance clicked");

  const statusElement = document.getElementById("status");
  
  if (!tokenFromURL) {
    console.error("❌ No token in URL");
    showStatus("❌ Token missing! Please scan the QR code again.", "error");
    return;
  }

  const name = document.getElementById("studentName").value;
  const roll = document.getElementById("rollNo").value;

  console.log("📤 Submitting:", { name, roll, token: tokenFromURL });

  const submitBtn = event.target.querySelector('button[type="submit"]');
  submitBtn.disabled = true;
  submitBtn.innerHTML = '<span class="btn-icon">⏳</span> Marking...';

  try {
    const url = `${BACKEND_URL}/mark_attendance`;
    console.log("📤 Sending to:", url);
    
    const response = await fetch(url, {
      method: "POST",
      headers: { 
        "Content-Type": "application/json",
        "ngrok-skip-browser-warning": "69420"
      },
      body: JSON.stringify({
        student_name: name,
        roll: roll,
        token: tokenFromURL
      })
    });

    console.log("📥 Response status:", response.status);
    
    const result = await response.json();
    console.log("📥 Result:", result);
    
    if (result.status === "success") {
      showStatus(`✅ ${result.message}`, "success");
      document.getElementById("studentName").value = "";
      document.getElementById("rollNo").value = "";
    } else {
      showStatus(`❌ ${result.message}`, "error");
    }

  } catch (error) {
    console.error("❌ Error:", error);
    showStatus("❌ Failed to connect. Please check your internet!", "error");
  } finally {
    submitBtn.disabled = false;
    submitBtn.innerHTML = '<span class="btn-icon">✓</span> Mark My Attendance';
  }
}

// TEACHER: Generate QR Code
async function generateQR() {
  console.log("🎯 Generate QR clicked");
  
  const statusElement = document.getElementById("status");
  const qrBox = document.getElementById("qrBox");
  const qrImage = document.getElementById("qrImage");
  
  // Get subject name from input field
  const subjectInput = document.getElementById("subjectName");
  const subject = subjectInput ? subjectInput.value.trim() : "General";
  
  if (!subject) {
    showStatus("⚠️ Please enter a subject name!", "error");
    return;
  }

  showStatus("⏳ Generating QR Code...", "success");

  try {
    const url = `${BACKEND_URL}/generate_token`;
    console.log("📤 Calling:", url);
    console.log("📚 Subject:", subject);
    
    const response = await fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "ngrok-skip-browser-warning": "69420"
      },
      body: JSON.stringify({
        subject: subject
      })
    });

    console.log("📥 Response status:", response.status);

    if (!response.ok) {
      const text = await response.text();
      console.error("❌ Error response:", text);
      throw new Error(`Server error: ${response.status}`);
    }

    const data = await response.json();
    console.log("📥 Token data:", data);

    if (data.status !== "success") {
      throw new Error("Token generation failed");
    }

    // Get QR image
    const qrUrl = `${BACKEND_URL}/get_qr?t=${Date.now()}`;
    console.log("🖼️ Fetching QR from:", qrUrl);
    
    const imgResponse = await fetch(qrUrl, {
      headers: {
        "ngrok-skip-browser-warning": "69420"
      }
    });
    
    console.log("📥 QR response status:", imgResponse.status);
    
    if (!imgResponse.ok) {
      throw new Error(`QR fetch failed: ${imgResponse.status}`);
    }
    
    const blob = await imgResponse.blob();
    console.log("📥 QR blob size:", blob.size, "bytes");
    
    const objectUrl = URL.createObjectURL(blob);
    qrImage.src = objectUrl;
    
    qrImage.onload = function() {
      console.log("✅ QR loaded!");
      qrBox.classList.remove("hidden");
      showStatus(`✅ QR Code generated for ${subject}!`, "success");
      startTimer(120);
    };

    qrImage.onerror = function(e) {
      console.error("❌ QR image load failed:", e);
      showStatus("❌ QR image failed to load!", "error");
    };

  } catch (error) {
    console.error("❌ Error:", error);
    showStatus(`❌ Error: ${error.message}`, "error");
  }
}

// TEACHER: Open Google Sheets
function openGoogleSheets() {
  console.log("📊 Opening Google Sheets...");
  
  const sheetUrl = `https://docs.google.com/spreadsheets/d/${GOOGLE_SHEET_ID}/edit`;
  console.log("📊 Opening:", sheetUrl);
  
  // Open in new tab
  window.open(sheetUrl, '_blank');
}

// Timer countdown
function startTimer(duration) {
  clearInterval(timerInterval);
  
  let timeLeft = duration;
  const timerElement = document.getElementById("timer");
  
  if (!timerElement) return;

  timerInterval = setInterval(() => {
    const minutes = Math.floor(timeLeft / 60);
    const seconds = timeLeft % 60;
    
    timerElement.textContent = `${minutes}:${seconds.toString().padStart(2, '0')}`;
    
    if (timeLeft <= 0) {
      clearInterval(timerInterval);
      timerElement.textContent = "Expired";
      showStatus("⏰ QR expired. Generate a new one!", "error");
    }
    
    timeLeft--;
  }, 1000);
}

// Show status message
function showStatus(message, type) {
  const statusElement = document.getElementById("status");
  if (!statusElement) return;
  
  statusElement.textContent = message;
  statusElement.className = `status-message show ${type}`;
  
  if (type === "success") {
    setTimeout(() => {
      statusElement.classList.remove("show");
    }, 5000);
  }
}

// Check if on student page
if (window.location.pathname.includes("student.html")) {
  console.log("📄 Student page loaded");
  if (tokenFromURL) {
    console.log("✅ Token:", tokenFromURL);
  } else {
    console.warn("⚠️ No token in URL");
    showStatus("⚠️ No token found. Scan the QR code again.", "error");
  }
}

// Test connection on load
console.log("🧪 Testing backend...");
fetch(`${BACKEND_URL}/`, {
  headers: {
    "ngrok-skip-browser-warning": "69420"
  }
})
.then(r => r.json())
.then(data => {
  console.log("✅ Backend connected:", data);
})
.catch(err => {
  console.error("❌ Backend connection failed:", err);
  console.error("⚠️ Make sure Flask and ngrok are running!");
});