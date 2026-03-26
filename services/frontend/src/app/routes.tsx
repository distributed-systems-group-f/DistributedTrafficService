import { createBrowserRouter, Navigate } from 'react-router';
import { SignIn }      from './pages/SignIn';
import { Register }    from './pages/Register';
import { BookJourney } from './pages/BookJourney';
import { MyJourneys }  from './pages/MyJourneys';
import { VerifyPlate } from './pages/VerifyPlate';
import { Root }        from './Root';

export const router = createBrowserRouter([
  {
    path: '/',
    element: <Root />,
    children: [
      { index: true,       element: <Navigate to="/signin" replace /> },
      { path: 'signin',    element: <SignIn /> },
      { path: 'register',  element: <Register /> },
      { path: 'book',      element: <BookJourney /> },
      { path: 'journeys',  element: <MyJourneys /> },
      { path: 'verify',    element: <VerifyPlate /> },
    ],
  },
]);
