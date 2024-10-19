import React, { useState } from 'react';
import Cookies from 'js-cookie';
import { login } from '../services/LoginService';
import { useNavigate } from 'react-router-dom';

const Login = () => {
  //#region Properties
  const [loading, setLoading] = useState(false);

  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');

  const navigate = useNavigate();
  //#endregion

  //#region Event Handlers
  const handleSubmit = async (e) => {
    e.preventDefault();
    const loginData = {
      username: username,
      password: password,
    };

    try {
      setLoading(true);
      const response = await login(loginData);
      const { refresh_token, access_token, author_id } = response;

      Cookies.set('author_id', author_id);
      Cookies.set('access_token', access_token);
      Cookies.set('refresh_token', refresh_token);

      setLoading(false);
      navigate('/');
      console.log('Login successful:', response);
    } catch (error) {
      console.error('Login failed:', error);
    }
  };

  return (
    <div className="login-container">
      <h2>Login</h2>
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label>Username</label>
          <input
            type="text"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            required
          />
        </div>
        <div className="form-group">
          <label>Password</label>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
        </div>
        <button type="submit" disabled={loading}>
          Login
        </button>
      </form>
    </div>
  );
};

export default Login;
