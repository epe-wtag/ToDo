import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useCookies } from 'react-cookie';

const useAuthRedirect = () => {
  const navigate = useNavigate();
  const [cookies] = useCookies(['id', 'is_admin']);
  const [checkedAuth, setCheckedAuth] = useState(false);

  useEffect(() => {
    if (checkedAuth) {
      if (!cookies.id) {
        navigate('/login');
      }
    } else {
      setCheckedAuth(true);
    }
  }, [cookies, navigate, checkedAuth]);
};

export default useAuthRedirect;
