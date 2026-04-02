import { useId, useState } from "react";

type Props = {
  id?: string;
  value: string;
  onChange: (value: string) => void;
  autoComplete?: "current-password" | "new-password";
  required?: boolean;
};

export function PasswordField({
  id: idProp,
  value,
  onChange,
  autoComplete = "current-password",
  required,
}: Props) {
  const [visible, setVisible] = useState(false);
  const genId = useId();
  const inputId = idProp ?? genId;

  return (
    <div className="field-password">
      <input
        id={inputId}
        type={visible ? "text" : "password"}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        autoComplete={autoComplete}
        required={required}
      />
      <button
        type="button"
        className="btn-password-toggle"
        onClick={() => setVisible((v) => !v)}
        aria-label={visible ? "Ocultar senha" : "Mostrar senha"}
        aria-pressed={visible}
      >
        {visible ? "Ocultar" : "Ver"}
      </button>
    </div>
  );
}
