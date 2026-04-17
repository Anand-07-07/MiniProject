const navLinks = document.querySelectorAll('.nav-links a');
const sections = document.querySelectorAll('main section');

function updateActiveNav() {
  const scrollPosition = window.scrollY + 120;
  let currentId = 'home';

  sections.forEach((section) => {
    if (section.offsetTop <= scrollPosition) {
      currentId = section.id;
    }
  });

  navLinks.forEach((link) => {
    link.classList.toggle('active', link.getAttribute('href') === `#${currentId}`);
  });
}

window.addEventListener('scroll', updateActiveNav);
window.addEventListener('load', updateActiveNav);
