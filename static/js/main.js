// ===== NAVBAR SCROLL EFFECT =====
document.addEventListener('DOMContentLoaded', function() {
    const navbar = document.getElementById('mainNav');
    
    // ===== DROPDOWN TOGGLE FOR TOUCH/MOBILE DEVICES =====
    // On touch devices, click is needed since CSS :hover doesn't work
    function isTouchDevice() {
        return 'ontouchstart' in window || navigator.maxTouchPoints > 0;
    }
    
    if (isTouchDevice()) {
        document.querySelectorAll('.navbar .dropdown-toggle').forEach(function(dropdownToggle) {
            dropdownToggle.addEventListener('click', function(e) {
                e.preventDefault();
                e.stopPropagation();
                
                const parent = this.closest('.dropdown');
                
                // Close other open dropdowns
                document.querySelectorAll('.navbar .dropdown-menu.show').forEach(function(openMenu) {
                    const openParent = openMenu.closest('.dropdown');
                    if (openParent !== parent) {
                        openMenu.classList.remove('show');
                        openMenu.style.visibility = '';
                        openMenu.style.opacity = '';
                        openMenu.style.transform = '';
                        openMenu.style.pointerEvents = '';
                    }
                });
                
                // Toggle the current dropdown
                const dropdownMenu = this.nextElementSibling;
                if (dropdownMenu && dropdownMenu.classList.contains('dropdown-menu')) {
                    dropdownMenu.classList.toggle('show');
                    if (dropdownMenu.classList.contains('show')) {
                        dropdownMenu.style.visibility = 'visible';
                        dropdownMenu.style.opacity = '1';
                        dropdownMenu.style.transform = 'translateY(0)';
                        dropdownMenu.style.pointerEvents = 'all';
                    } else {
                        dropdownMenu.style.visibility = '';
                        dropdownMenu.style.opacity = '';
                        dropdownMenu.style.transform = '';
                        dropdownMenu.style.pointerEvents = '';
                    }
                }
            });
        });
        
        // Close dropdowns when clicking outside (touch only)
        document.addEventListener('click', function(e) {
            if (!e.target.closest('.navbar .dropdown')) {
                document.querySelectorAll('.navbar .dropdown-menu.show').forEach(function(menu) {
                    menu.classList.remove('show');
                    menu.style.visibility = '';
                    menu.style.opacity = '';
                    menu.style.transform = '';
                    menu.style.pointerEvents = '';
                });
            }
        });
    }
    
    if (navbar) {
        window.addEventListener('scroll', function() {
            if (window.scrollY > 50) {
                navbar.classList.add('scrolled');
            } else {
                navbar.classList.remove('scrolled');
            }
        });
    }
    
    // ===== SCROLL-TRIGGERED ANIMATIONS =====
    const animateElements = document.querySelectorAll('.animate-on-scroll, .animate-fadeIn, .animate-fadeInLeft, .animate-fadeInRight, .animate-slideUp, .animate-scaleIn');
    
    // Remove initial animation classes so IntersectionObserver handles them
    animateElements.forEach(el => {
        // Store the animation class
        const animClass = Array.from(el.classList).find(cls => 
            cls.startsWith('animate-') && cls !== 'animate-float' && cls !== 'animate-pulseGlow'
        );
        if (animClass && el.dataset.animClass === undefined) {
            el.dataset.animClass = animClass;
            el.classList.remove(animClass);
            el.style.opacity = '0';
        }
    });
    
    // Handle stagger-children
    document.querySelectorAll('.stagger-children').forEach(parent => {
        parent.querySelectorAll(':scope > *').forEach(child => {
            if (child.dataset.animClass === undefined) {
                child.dataset.animClass = 'animate-fadeIn';
                child.style.opacity = '0';
            }
        });
    });
    
    // Create Intersection Observer
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const el = entry.target;
                
                // Check if it's a stagger-children container
                if (el.classList.contains('stagger-children')) {
                    const children = el.querySelectorAll(':scope > *');
                    children.forEach((child, index) => {
                        const delay = (index + 1) * 0.1;
                        child.style.animationDelay = `${delay}s`;
                        child.style.opacity = '1';
                        child.style.animation = `fadeIn 0.6s ease forwards`;
                        child.style.animationDelay = `${delay}s`;
                    });
                } else {
                    // Regular animated element
                    const animClass = el.dataset.animClass || 'animate-fadeIn';
                    el.style.opacity = '1';
                    el.style.animation = `${animClass.replace('animate-', '')} 0.8s ease forwards`;
                }
                
                // Unobserve after animation
                observer.unobserve(el);
            }
        });
    }, {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    });
    
    // Observe all elements that need animation
    document.querySelectorAll('.animate-on-scroll, .stagger-children, [data-anim-class]').forEach(el => {
        observer.observe(el);
    });
    
    // Also observe direct children of stagger-children that are already visible
    document.querySelectorAll('.stagger-children > *').forEach(el => {
        if (el.dataset.animClass !== undefined) {
            observer.observe(el);
        }
    });
    
    // ===== SMOOTH SCROLL FOR ANCHOR LINKS =====
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            const targetId = this.getAttribute('href');
            if (targetId !== '#') {
                const targetElement = document.querySelector(targetId);
                if (targetElement) {
                    e.preventDefault();
                    targetElement.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
                }
            }
        });
    });
    
    // ===== TOOLTIP INITIALIZATION =====
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // ===== PARALLAX EFFECT ON HERO =====
    const heroSection = document.querySelector('.hero-section');
    if (heroSection) {
        window.addEventListener('scroll', function() {
            const scrolled = window.pageYOffset;
            const rate = scrolled * 0.3;
            heroSection.style.transform = `translate3d(0, ${rate * 0.5}px, 0)`;
        });
    }
    
    // ===== PAGE LOAD ANIMATION =====
    document.body.classList.add('page-loaded');
    
    // ===== AUTO-DISMISS FLASH MESSAGES =====
    setTimeout(function() {
        const alerts = document.querySelectorAll('.flash-messages .alert');
        alerts.forEach(function(alert) {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        });
    }, 6000);
});