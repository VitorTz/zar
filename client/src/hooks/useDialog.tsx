import { useState, type ReactNode } from "react";
import { Alert, Confirm } from "../components/Dialog";

type ConfirmOptions = {
  message: string;
  resolve: (value: boolean) => void;
};

export const useDialog = () => {
  const [alertMessage, setAlertMessage] = useState<string | null>(null);
  const [alertResolve, setAlertResolve] = useState<(() => void) | null>(null);
  const [confirmOptions, setConfirmOptions] = useState<ConfirmOptions | null>(null);
  
  const showAlert = (message: string): Promise<void> => {
    return new Promise<void>((resolve) => {
      setAlertMessage(message);
      setAlertResolve(() => resolve);
    });
  };
  
  const showConfirm = (message: string): Promise<boolean> => {
    return new Promise<boolean>((resolve) => {
      setConfirmOptions({ message, resolve });
    });
  };

  const AlertRenderer: ReactNode = alertMessage ? (
    <Alert
      message={alertMessage}
      onClose={() => {
        setAlertMessage(null);
        alertResolve?.();
        setAlertResolve(null);
      }}
    />
  ) : null;

  const ConfirmRenderer: ReactNode = confirmOptions ? (
    <Confirm
      message={confirmOptions.message}
      onCancel={() => {
        confirmOptions.resolve(false);
        setConfirmOptions(null);
      }}
      onConfirm={() => {
        confirmOptions.resolve(true);
        setConfirmOptions(null);
      }}
    />
  ) : null;

  return { showAlert, showConfirm, AlertRenderer, ConfirmRenderer };
};
