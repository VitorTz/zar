import type { NotificationState } from "../types/notification";


interface NotificationContainerProps {
    notifications: NotificationState[]
}


const NotificationContainer = ({ notifications }: NotificationContainerProps) => (
  <div className="notification-container">
    {notifications.map((n) => (
      <div key={n.id} className={`notification notification-${n.type}`}>
        {n.message}
      </div>
    ))}
  </div>
);


export default NotificationContainer;