const flags = {
  AU: "🇦🇺",
  BR: "🇧🇷",
  CA: "🇨🇦",
  CH: "🇨🇭",
  DE: "🇩🇪",
  DK: "🇩🇰",
  ES: "🇪🇸",
  FI: "🇫🇮",
  FR: "🇫🇷",
  GB: "🇬🇧",
  IE: "🇮🇪",
  IN: "🇮🇳",
  IR: "🇮🇷",
  MX: "🇲🇽",
  NL: "🇳🇱",
  NO: "🇳🇴",
  NZ: "🇳🇿",
  RS: "🇷🇸",
  TR: "🇹🇷",
  UA: "🇺🇦",
  US: "🇺🇸"
};

async function getRandomUser() {
  // Get Card ID
  const card = document.getElementById("userCard");

  // Set a delay and call it:  await delay(250);
  const delay = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
  card.classList.add("animate-out");

  card.classList.remove("animate-in");
  await delay(200);
  // Wait for the animation to finish
  card.innerHTML = `
        <div class="loading">
          <div class="spinner"></div>
          <p class="loading-text">Loading...</p>
        </div>
      `;

  try {
    // Fetch 1 users from the API
    const response = await fetch("https://randomuser.me/api/?results=1");
    const data = await response.json();

    // Pick a random user from the 5 results
    const randomIndex = Math.floor(Math.random() * data.results.length);
    const user = data.results[randomIndex];

    const bg = document.getElementById("darken");

    bg.classList.add("show");

    // Display the user
    const flag = flags[user.nat] || "🌍";
    const name = `${user.name.title} ${user.name.first}${user.name.last}`;
    const location = `${user.location.city}, ${user.location.country}`;
    const birthday = new Date(user.dob.date).toLocaleDateString();
    console.log(`${user.picture.large}`);
    const pic = user.picture.large;
    bg.style.opacity = "0";
    setTimeout(function () {
      bg.style.backgroundImage = "url(" + pic + ")";
      bg.style.opacity = "1";
    }, 700);

    card.innerHTML = `
          <div class="card-header">
            <img class="avatar" src="${user.picture.large}" alt="${name}">
          </div>
          <div class="card-body">
            <h2 class="name">${name}<span class="flag">${flag}</span></h2>
            <p class="location">📍 ${location}</p>
            
            <div class="info-grid">
              <div class="info-item">
                <span class="info-icon">📧</span>
                <div class="info-content">
                  <div class="info-label">Email</div>
                  <div class="info-value">${user.email}</div>
                </div>
              </div>
              
              <div class="info-item">
                <span class="info-icon">📱</span>
                <div class="info-content">
                  <div class="info-label">Phone</div>
                  <div class="info-value">${user.cell}</div>
                </div>
              </div>
              
              <div class="info-item">
                <span class="info-icon">🎂</span>
                <div class="info-content">
                  <div class="info-label">Birthday</div>
                  <div class="info-value">${birthday} (${user.dob.age} years old)</div>
                </div>
              </div>
              
              <div class="info-item">
                <span class="info-icon">👤</span>
                <div class="info-content">
                  <div class="info-label">Username</div>
                  <div class="info-value">${user.login.username}</div>
                </div>
              </div>
            </div>
            
            <button class="btn" onclick="getRandomUser()">🎲 Get Random User</button><br>
            <hr>
             <footer class="footer">
    <a href="#" id="twit" aria-label="Twitter">
      <svg viewBox="0 0 24 24" fill="currentColor">
        <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z" />
      </svg>
    </a>
    <a href="#" aria-label="GitHub">
      <svg viewBox="0 0 24 24" fill="currentColor">
        <path d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.531 1.032 1.531 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z" />
      </svg>
    </a>
    <a href="#" aria-label="LinkedIn">
      <svg viewBox="0 0 24 24" fill="currentColor">
        <path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z" />
      </svg>
    </a>
  </footer>
          </div>
        `;
  } catch (error) {
    card.innerHTML = `
          <div class="loading">
            <p class="loading-text">❌ Error loading user</p>
            <button class="btn" onclick="getRandomUser()">Try Again</button>
          </div>
        `;
  }
  setTimeout(() => {
    card.classList.remove("animate-out");
    card.classList.add("animate-in");
  }, 0);
}

// Load a random user when page loads
getRandomUser();
