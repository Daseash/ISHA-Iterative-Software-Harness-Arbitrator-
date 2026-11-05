"use client";

import React, {
  useState,
  useRef,
  useEffect,
  useImperativeHandle,
  forwardRef,
} from "react";
import { motion, AnimatePresence } from "framer-motion";
import { cn } from "../../lib/utils";

export type CursorVariant = "line" | "block" | "underline" | "glow";
export type CharAnimationPreset =
  | "spring"
  | "bounce"
  | "fade"
  | "slide"
  | "wave"
  | "typewriter";
export type InputVariant =
  | "default"
  | "ghost"
  | "outline"
  | "filled"
  | "terminal"
  | "minimal"
  | "pill";

export interface AnimatedInputProps
  extends Omit<React.InputHTMLAttributes<HTMLInputElement | HTMLTextAreaElement>, "onChange"> {
  color?: string;
  caretWidth?: number;
  radius?: number;
  cursorVariant?: CursorVariant;
  blinkSpeed?: number;
  charAnimation?: CharAnimationPreset;
  inputVariant?: InputVariant;
  fieldClassName?: string;
  multiline?: boolean;
  limitToWidth?: boolean;
  value?: string;
  defaultValue?: string;
  onChange?: (value: string) => void;
  placeholder?: string;
}

export interface AnimatedInputRef {
  focus: () => void;
  blur: () => void;
  inputElement: HTMLInputElement | HTMLTextAreaElement | null;
}

const getCharVariants = (preset: CharAnimationPreset) => {
  switch (preset) {
    case "bounce":
      return {
        initial: { opacity: 0, y: -10, scaleY: 1.3 },
        animate: { opacity: 1, y: 0, scaleY: 1 },
        exit: { opacity: 0, y: 8, scaleY: 0.8 },
        transition: { type: "spring" as const, stiffness: 600, damping: 15 },
      };
    case "fade":
      return {
        initial: { opacity: 0 },
        animate: { opacity: 1 },
        exit: { opacity: 0 },
        transition: { duration: 0.15 },
      };
    case "slide":
      return {
        initial: { opacity: 0, x: -6 },
        animate: { opacity: 1, x: 0 },
        exit: { opacity: 0, x: 6 },
        transition: { duration: 0.16, ease: "easeOut" as const },
      };
    case "wave":
      return {
        initial: { opacity: 0, y: 8 },
        animate: { opacity: 1, y: 0 },
        exit: { opacity: 0, y: -8 },
        transition: { type: "spring" as const, stiffness: 450, damping: 22 },
      };
    case "typewriter":
      return {
        initial: { opacity: 0 },
        animate: { opacity: 1 },
        exit: { opacity: 0 },
        transition: { duration: 0.01 },
      };
    case "spring":
    default:
      return {
        initial: { opacity: 0, y: -6, scale: 0.6 },
        animate: { opacity: 1, y: 0, scale: 1 },
        exit: { opacity: 0, y: 6, scale: 0.6 },
        transition: { type: "spring" as const, stiffness: 500, damping: 25 },
      };
  }
};

const getVariantClasses = (variant?: InputVariant) => {
  switch (variant) {
    case "ghost":
      return "border-transparent bg-transparent hover:bg-neutral-100/50 dark:hover:bg-neutral-900/50";
    case "outline":
      return "border border-neutral-300 dark:border-neutral-700 bg-transparent focus-within:border-red-600 dark:focus-within:border-red-500";
    case "filled":
      return "border border-transparent bg-neutral-100 dark:bg-neutral-900 focus-within:border-neutral-300 dark:focus-within:border-neutral-700";
    case "terminal":
      return "border border-neutral-800 bg-neutral-950 text-emerald-400 font-mono shadow-inner";
    case "minimal":
      return "border-none bg-transparent p-0 shadow-none";
    case "pill":
      return "rounded-full border border-neutral-300 dark:border-neutral-700 bg-white/80 dark:bg-neutral-900/80 px-4 py-2";
    case "default":
    default:
      return "rounded-xl border border-neutral-300/80 dark:border-neutral-800 bg-white/60 dark:bg-neutral-950/60 px-3.5 py-2.5 shadow-sm focus-within:ring-2 focus-within:ring-red-600/30";
  }
};

export const AnimatedInput = forwardRef<AnimatedInputRef, AnimatedInputProps>(
  (
    {
      color = "#dc2626",
      caretWidth = 2,
      radius = 2,
      cursorVariant = "line",
      blinkSpeed = 530,
      charAnimation = "spring",
      inputVariant = "default",
      className = "",
      fieldClassName = "",
      multiline = false,
      value: controlledValue,
      defaultValue = "",
      onChange,
      placeholder = "Type something…",
      disabled = false,
      ...props
    },
    ref,
  ) => {
    const isControlled = controlledValue !== undefined;
    const [internalValue, setInternalValue] = useState<string>(
      isControlled ? controlledValue : defaultValue,
    );
    const textValue = isControlled ? controlledValue : internalValue;

    const [isFocused, setIsFocused] = useState(false);
    const [cursorIndex, setCursorIndex] = useState(textValue.length);
    const [isBlinking, setIsBlinking] = useState(true);

    const nativeInputRef = useRef<HTMLInputElement | HTMLTextAreaElement | null>(null);
    const blinkTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

    useImperativeHandle(ref, () => ({
      focus: () => nativeInputRef.current?.focus(),
      blur: () => nativeInputRef.current?.blur(),
      inputElement: nativeInputRef.current,
    }));

    // Pause blinking while actively typing
    const resetBlink = () => {
      setIsBlinking(false);
      if (blinkTimerRef.current) clearTimeout(blinkTimerRef.current);
      blinkTimerRef.current = setTimeout(() => {
        setIsBlinking(true);
      }, 400);
    };

    useEffect(() => {
      return () => {
        if (blinkTimerRef.current) clearTimeout(blinkTimerRef.current);
      };
    }, []);

    const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
      const nextVal = e.target.value;
      if (!isControlled) {
        setInternalValue(nextVal);
      }
      setCursorIndex(e.target.selectionStart ?? nextVal.length);
      resetBlink();
      onChange?.(nextVal);
    };

    const handleSelect = (e: React.SyntheticEvent<HTMLInputElement | HTMLTextAreaElement>) => {
      const target = e.currentTarget;
      setCursorIndex(target.selectionStart ?? textValue.length);
      resetBlink();
    };

    const charVariants = getCharVariants(charAnimation);

    // Render caret styling according to cursorVariant
    const renderCaret = () => {
      if (!isFocused || disabled) return null;

      const baseCaretStyle: React.CSSProperties = {
        backgroundColor: color,
        borderRadius: `${radius}px`,
      };

      if (cursorVariant === "glow") {
        baseCaretStyle.boxShadow = `0 0 8px ${color}, 0 0 14px ${color}80`;
      }

      return (
        <motion.span
          animate={{ opacity: isBlinking ? [1, 0, 1] : 1 }}
          transition={{
            duration: blinkSpeed / 500,
            repeat: isBlinking ? Infinity : 0,
            ease: "easeInOut",
          }}
          className={cn(
            "pointer-events-none inline-block align-middle select-none shrink-0",
            cursorVariant === "underline"
              ? "h-[2.5px] w-2 -mb-2"
              : cursorVariant === "block"
              ? "h-[1.15em] w-2.5 opacity-60"
              : "h-[1.25em]",
          )}
          style={{
            ...baseCaretStyle,
            width:
              cursorVariant === "underline"
                ? 10
                : cursorVariant === "block"
                ? 9
                : caretWidth,
          }}
        />
      );
    };

    const chars = textValue.split("");

    return (
      <div
        className={cn(
          "relative flex items-center transition-all cursor-text",
          getVariantClasses(inputVariant),
          disabled && "opacity-50 cursor-not-allowed",
          className,
        )}
        onClick={() => nativeInputRef.current?.focus()}
      >
        {/* Transparent Native Input Overlay for full IME, keyboard, selection support */}
        {multiline ? (
          <textarea
            ref={nativeInputRef as React.RefObject<HTMLTextAreaElement>}
            value={textValue}
            onChange={handleChange}
            onSelect={handleSelect}
            onFocus={() => {
              setIsFocused(true);
              resetBlink();
            }}
            onBlur={() => setIsFocused(false)}
            disabled={disabled}
            className={cn(
              "absolute inset-0 w-full h-full opacity-0 z-20 resize-none cursor-text",
              fieldClassName,
            )}
            {...(props as React.TextareaHTMLAttributes<HTMLTextAreaElement>)}
          />
        ) : (
          <input
            ref={nativeInputRef as React.RefObject<HTMLInputElement>}
            type="text"
            value={textValue}
            onChange={handleChange}
            onSelect={handleSelect}
            onFocus={() => {
              setIsFocused(true);
              resetBlink();
            }}
            onBlur={() => setIsFocused(false)}
            disabled={disabled}
            className={cn(
              "absolute inset-0 w-full h-full opacity-0 z-20 cursor-text",
              fieldClassName,
            )}
            {...(props as React.InputHTMLAttributes<HTMLInputElement>)}
          />
        )}

        {/* Visible Animated Text and Dynamic Caret Stage */}
        <div
          className={cn(
            "relative z-10 flex items-center flex-wrap min-w-0 select-none overflow-hidden",
            fieldClassName,
          )}
        >
          {textValue.length === 0 ? (
            <div className="flex items-center min-w-0">
              {cursorIndex === 0 && renderCaret()}
              <span className="opacity-40 truncate pointer-events-none">
                {placeholder}
              </span>
            </div>
          ) : (
            <div className="inline-flex items-center flex-wrap leading-tight">
              <AnimatePresence mode="popLayout" initial={false}>
                {chars.map((char, index) => {
                  const showCaretBefore = isFocused && cursorIndex === index;
                  return (
                    <React.Fragment key={`${index}-${char}`}>
                      {showCaretBefore && renderCaret()}
                      <motion.span
                        layout
                        initial={charVariants.initial}
                        animate={charVariants.animate}
                        exit={charVariants.exit}
                        transition={charVariants.transition}
                        className="inline-block whitespace-pre will-change-transform"
                      >
                        {char === " " ? "\u00A0" : char}
                      </motion.span>
                    </React.Fragment>
                  );
                })}
              </AnimatePresence>
              {isFocused && cursorIndex >= textValue.length && renderCaret()}
            </div>
          )}
        </div>
      </div>
    );
  },
);

AnimatedInput.displayName = "AnimatedInput";

export const TextCursorTypingInput = AnimatedInput;
export default AnimatedInput;
