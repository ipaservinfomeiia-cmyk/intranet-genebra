// js/auth.js
document.addEventListener('DOMContentLoaded', () => {
    const backendUrl = 'https://intranet-genebra.onrender.com';
    const token = localStorage.getItem('jwt_token');
    const currentPage = window.location.pathname.split('/').pop();

    // Se estamos na página de login
    if (currentPage === 'login.html') {
        // Se já tem token, redireciona para a página principal
        if (token) {
            window.location.href = 'index.html';
            return;
        }

        const loginForm = document.getElementById('login-form');
        const errorMessage = document.getElementById('error-message');

        loginForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            errorMessage.textContent = '';
            const username = loginForm.username.value;
            const password = loginForm.password.value;

            try {
                const response = await fetch(`${backendUrl}/login`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ username, password })
                });

                const data = await response.json();

                if (!response.ok) {
                    throw new Error(data.msg || 'Erro ao tentar fazer login.');
                }
                
                localStorage.setItem('jwt_token', data.access_token);
                window.location.href = 'index.html'; // Redireciona para a página principal

            } catch (error) {
                errorMessage.textContent = error.message;
            }
        });

    // Se estamos em qualquer outra página
    } else {
        // Se NÃO tem token, redireciona para a página de login
        if (!token) {
            window.location.href = 'login.html';
            return;
        }

        // Lógica de Logout
        const logoutButton = document.getElementById('logout-button'); // Encontra o botão pelo seu ID
if (logoutButton) {
    logoutButton.addEventListener('click', (e) => {
        e.preventDefault();
        localStorage.removeItem('jwt_token');
        window.location.href = 'login.html';
            });
        }
    }
});

