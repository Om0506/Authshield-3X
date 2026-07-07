document.addEventListener('DOMContentLoaded', function () {
  const sidebarLinks = document.querySelectorAll('.nav-item');
  const savedPage = localStorage.getItem('selectedPage') || 'dashboard.html';
  loadPage(savedPage);

  sidebarLinks.forEach((link) => {
    link.addEventListener('click', function (e) {
      e.preventDefault();
      const page = this.getAttribute('data-page');
      localStorage.setItem('selectedPage', page);
      loadPage(page);
    });
  });

  function loadPage(page) {
    console.log('Loading page:', page);

    fetch(`${page}?v=${new Date().getTime()}`) // Cache-busting trick
      .then((response) => {
        if (!response.ok) throw new Error('Page not found');
        return response.text();
      })
      .then((data) => {
        const contentElement = document.querySelector('.content1');
        contentElement.innerHTML = data; // Inject new content

        executeInlineScripts(data); // Re-execute the scripts on the new page

        if (page === 'dashboard.html') {
          updateDashboardStats(); // Run Firebase logic after loading user-management.html
        }
        if (page === 'user-management.html') {
          initializeFirebaseUserTable(); // Run Firebase logic after loading user-management.html
        }
        if (page === 'entry-logs.html') {
          initializeFirebaseLogsTable(); // Run Firebase logic after loading user-management.html
        }
        if (page === 'door-control.html') {
          console.log("Loading door-control page...");
        
          Promise.all([fetchOffHours(), fetchDoorStatus()])
            .then(() => console.log("Both functions executed successfully"))
            .catch((error) => console.error("Error in simultaneous fetching:", error));
        }
        if (page === 'alerts-notifications.html') {
          initializeFirebaseNotification(); // Run Firebase logic after loading user-management.html
        }
       
        
        highlightActivePage(page); // Update sidebar highlight
      })
      .catch((error) => {
        console.error('Error loading page:', error);
      });
  }

   
  function executeInlineScripts(data) {
    const tempDiv = document.createElement('div');
    tempDiv.innerHTML = data;
    const scripts = tempDiv.querySelectorAll('script');

    scripts.forEach((script) => {
      const newScript = document.createElement('script');
      if (script.src) {
        newScript.src = script.src; // Handle external scripts
      } else {
        newScript.innerHTML = script.innerHTML; // Handle inline scripts
      }
      document.body.appendChild(newScript);
    });
  }

  function highlightActivePage(page) {
    sidebarLinks.forEach((link) => {
      if (link.getAttribute('data-page') === page) {
        link.classList.add('active');
      } else {
        link.classList.remove('active');
      }
    });
  }
});
 