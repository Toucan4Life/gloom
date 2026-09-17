import {
  forwardRef,
  useCallback,
  useEffect,
  useImperativeHandle,
  useRef,
  useState,
} from 'react';

const STATE_HIDDEN = 0;
const STATE_VISIBLE = 1;
const STATE_FADING = 2;

const DEFAULT_VISIBLE_MS = 3000;
const DEFAULT_FADE_MS = 2000;

interface MessageState {
  state: typeof STATE_HIDDEN | typeof STATE_VISIBLE | typeof STATE_FADING;
  className: string;
  text: string;
}

export interface MessageHandle {
  display(className: string, text: string): void;
  hide(): void;
}

export interface MessageProps {
  className?: string;
  visibleMs?: number;
  fadeMs?: number;
}

function getToneClasses(className: string): string {
  if (className.includes('alert-danger')) {
    return 'border-red-300 bg-red-50 text-red-800 dark:border-red-800 dark:bg-red-950/70 dark:text-red-100';
  }
  if (className.includes('alert-success')) {
    return 'border-emerald-300 bg-emerald-50 text-emerald-800 dark:border-emerald-800 dark:bg-emerald-950/70 dark:text-emerald-100';
  }
  if (className.includes('alert-warning')) {
    return 'border-amber-300 bg-amber-50 text-amber-800 dark:border-amber-800 dark:bg-amber-950/70 dark:text-amber-100';
  }
  return 'border-sky-300 bg-sky-50 text-sky-800 dark:border-sky-800 dark:bg-sky-950/70 dark:text-sky-100';
}

const Message = forwardRef<MessageHandle, MessageProps>(function Message(
  {
    className = '',
    visibleMs = DEFAULT_VISIBLE_MS,
    fadeMs = DEFAULT_FADE_MS,
  },
  ref,
) {
  const [messageState, setMessageState] = useState<MessageState>({
    state: STATE_HIDDEN,
    className: '',
    text: '',
  });
  const visibleTimeoutRef = useRef<number | null>(null);
  const fadeTimeoutRef = useRef<number | null>(null);

  const clearTimers = useCallback(() => {
    if (visibleTimeoutRef.current !== null) {
      window.clearTimeout(visibleTimeoutRef.current);
      visibleTimeoutRef.current = null;
    }
    if (fadeTimeoutRef.current !== null) {
      window.clearTimeout(fadeTimeoutRef.current);
      fadeTimeoutRef.current = null;
    }
  }, []);

  const hide = useCallback(() => {
    clearTimers();
    setMessageState((current) => (
      current.state === STATE_HIDDEN
        ? current
        : { ...current, state: STATE_HIDDEN }
    ));
  }, [clearTimers]);

  const display = useCallback((nextClassName: string, text: string) => {
    clearTimers();
    setMessageState({
      state: STATE_VISIBLE,
      className: nextClassName,
      text,
    });

    visibleTimeoutRef.current = window.setTimeout(() => {
      setMessageState((current) => ({
        ...current,
        state: STATE_FADING,
      }));

      fadeTimeoutRef.current = window.setTimeout(() => {
        setMessageState((current) => ({
          ...current,
          state: STATE_HIDDEN,
        }));
      }, fadeMs);
    }, visibleMs);
  }, [clearTimers, fadeMs, visibleMs]);

  useImperativeHandle(ref, () => ({ display, hide }), [display, hide]);

  useEffect(() => clearTimers, [clearTimers]);

  if (messageState.state === STATE_HIDDEN) {
    return null;
  }

  return (
    <div className='pointer-events-none fixed inset-x-0 bottom-4 z-50 flex justify-center px-4'>
      <div
        role='status'
        aria-live='polite'
        className={[
          'pointer-events-auto max-w-xl rounded-xl border px-4 py-3 text-center text-sm font-medium shadow-lg transition-opacity duration-500',
          messageState.state === STATE_FADING ? 'opacity-0' : 'opacity-100',
          getToneClasses(messageState.className),
          className,
        ].filter(Boolean).join(' ')}
      >
        {messageState.text}
      </div>
    </div>
  );
});

export default Message;
