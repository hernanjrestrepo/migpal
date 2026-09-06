/* ==========================================================================
   MigPAL — Internacionalización (es · pt · en)
   --------------------------------------------------------------------------
   Sin dependencias ni build step: un diccionario plano y una función `t()`.

   Cómo se aplica:
   - HTML estático: `data-i18n="clave"` reemplaza el texto del elemento.
     Variantes: `data-i18n-placeholder`, `data-i18n-title`, `data-i18n-aria`.
   - JS dinámico: `MigPAL.t('clave', { nombre: 'valor' })`.

   Sobre el español: se usa español neutro latinoamericano con "tú"
   (tienes, puedes, crea), NO voseo rioplatense (tenés, podés, creá). El
   producto se opera desde Colombia y el voseo suena extranjero al lector
   objetivo.

   El idioma se resuelve así, en orden: elección guardada del usuario →
   idioma del navegador → español.
   ========================================================================== */

window.MigPALi18n = (function () {
  'use strict';

  var LANG_KEY = 'migpal.lang';
  var SUPPORTED = ['es', 'pt', 'en'];

  var DICT = {
    /* ------------------------------------------------------------ común */
    'nav.how': { es: 'Cómo funciona', pt: 'Como funciona', en: 'How it works' },
    'nav.what': { es: 'Qué obtienes', pt: 'O que você recebe', en: 'What you get' },
    'nav.transparency': { es: 'Transparencia', pt: 'Transparência', en: 'Transparency' },
    'nav.login': { es: 'Iniciar sesión', pt: 'Entrar', en: 'Log in' },
    'nav.signup': { es: 'Crear cuenta', pt: 'Criar conta', en: 'Sign up' },
    'nav.myCase': { es: 'Ir a mi caso', pt: 'Ir para meu caso', en: 'Go to my case' },
    'nav.back': { es: '← Volver', pt: '← Voltar', en: '← Back' },
    'nav.logout': { es: 'Salir', pt: 'Sair', en: 'Log out' },
    'common.theme': { es: 'Cambiar tema', pt: 'Mudar tema', en: 'Toggle theme' },
    'common.language': { es: 'Idioma', pt: 'Idioma', en: 'Language' },
    'common.loading': { es: 'Cargando…', pt: 'Carregando…', en: 'Loading…' },
    'common.showPassword': { es: 'Mostrar contraseña', pt: 'Mostrar senha', en: 'Show password' },

    'title.login': { es: 'Iniciar sesión — MigPAL', pt: 'Entrar — MigPAL', en: 'Log in — MigPAL' },
    'title.signup': { es: 'Crear cuenta — MigPAL', pt: 'Criar conta — MigPAL', en: 'Sign up — MigPAL' },
    'title.case': { es: 'Mi caso — MigPAL', pt: 'Meu caso — MigPAL', en: 'My case — MigPAL' },
    'title.verify': { es: 'Verificar cuenta — MigPAL', pt: 'Verificar conta — MigPAL', en: 'Verify account — MigPAL' },
    'title.forgot': { es: 'Recuperar contraseña — MigPAL', pt: 'Recuperar senha — MigPAL', en: 'Recover password — MigPAL' },
    'title.reset': { es: 'Nueva contraseña — MigPAL', pt: 'Nova senha — MigPAL', en: 'New password — MigPAL' },
    'title.terms': { es: 'Términos y condiciones — MigPAL', pt: 'Termos e condições — MigPAL', en: 'Terms of service — MigPAL' },
    'title.privacy': { es: 'Política de privacidad — MigPAL', pt: 'Política de privacidade — MigPAL', en: 'Privacy policy — MigPAL' },

    /* ---------------------------------------------------------- landing */
    'landing.title': {
      es: 'MigPAL — Convierte tu proyecto migratorio en un plan concreto',
      pt: 'MigPAL — Transforme seu projeto migratório em um plano concreto',
      en: 'MigPAL — Turn your migration project into a concrete plan'
    },
    'landing.eyebrow': {
      es: 'Del diagnóstico al plan de ejecución',
      pt: 'Do diagnóstico ao plano de execução',
      en: 'From diagnosis to execution plan'
    },
    'landing.badgeNew': { es: 'Nuevo', pt: 'Novo', en: 'New' },
    'landing.h1a': { es: 'Tu proyecto migratorio,', pt: 'Seu projeto migratório,', en: 'Your migration project,' },
    'landing.h1b': {
      es: 'convertido en un plan concreto',
      pt: 'transformado em um plano concreto',
      en: 'turned into a concrete plan'
    },
    'landing.lead': {
      es: 'MigPAL evalúa tu perfil, te recomienda la ruta que mejor se ajusta y la convierte en pasos accionables — con dependencias, progreso y todo guardado para cuando vuelvas.',
      pt: 'O MigPAL avalia seu perfil, recomenda a rota que melhor se encaixa e a transforma em passos práticos — com dependências, progresso e tudo salvo para quando você voltar.',
      en: 'MigPAL evaluates your profile, recommends the route that fits you best, and turns it into actionable steps — with dependencies, progress, and everything saved for when you come back.'
    },
    'landing.ctaPrimary': { es: 'Crear mi cuenta gratis', pt: 'Criar minha conta grátis', en: 'Create my free account' },
    'landing.ctaSecondary': { es: 'Ver cómo funciona', pt: 'Ver como funciona', en: 'See how it works' },
    'landing.note': {
      es: 'Gratis para empezar · Sin tarjeta · Tu caso queda guardado',
      pt: 'Grátis para começar · Sem cartão · Seu caso fica salvo',
      en: 'Free to start · No card · Your case is saved'
    },
    'landing.stat1': { es: 'Etapas del recorrido', pt: 'Etapas do percurso', en: 'Journey stages' },
    'landing.stat2': { es: 'Cálculo determinístico', pt: 'Cálculo determinístico', en: 'Deterministic calculation' },
    'landing.stat3': { es: 'Decisiones tomadas por el LLM', pt: 'Decisões tomadas pelo LLM', en: 'Decisions made by the LLM' },
    'landing.stat4': { es: 'Veces que puedes volver', pt: 'Vezes que você pode voltar', en: 'Times you can come back' },
    'landing.howTitle': {
      es: 'Cuatro etapas, sin jerga ni promesas vacías',
      pt: 'Quatro etapas, sem jargão nem promessas vazias',
      en: 'Four stages, no jargon and no empty promises'
    },
    'landing.howSub': {
      es: 'Cada etapa produce algo concreto que queda guardado en tu caso. Nunca empiezas de cero.',
      pt: 'Cada etapa produz algo concreto que fica salvo no seu caso. Você nunca começa do zero.',
      en: 'Each stage produces something concrete that stays in your case. You never start over.'
    },
    'landing.step1Title': { es: 'Cuentas tu situación', pt: 'Você conta sua situação', en: 'You describe your situation' },
    'landing.step1Body': {
      es: 'Escribes en lenguaje natural: experiencia, estudios, familia, destino, finanzas. Sin formularios de 60 campos.',
      pt: 'Você escreve em linguagem natural: experiência, estudos, família, destino, finanças. Sem formulários de 60 campos.',
      en: 'You write in plain language: experience, education, family, destination, finances. No 60-field forms.'
    },
    'landing.step2Title': { es: 'Recibes tu evaluación', pt: 'Você recebe sua avaliação', en: 'You get your assessment' },
    'landing.step2Body': {
      es: 'Un puntaje calculado con reglas explícitas y versionadas, más los hallazgos concretos que las dispararon.',
      pt: 'Uma pontuação calculada com regras explícitas e versionadas, mais os achados concretos que as dispararam.',
      en: 'A score computed with explicit, versioned rules, plus the concrete findings behind it.'
    },
    'landing.step3Title': { es: 'Ves tu mejor ruta', pt: 'Você vê sua melhor rota', en: 'You see your best route' },
    'landing.step3Body': {
      es: 'La ruta con mejor ajuste a tu perfil, por qué se eligió, qué alternativas quedaron y cuál es el próximo paso.',
      pt: 'A rota com melhor encaixe no seu perfil, por que foi escolhida, quais alternativas ficaram e qual é o próximo passo.',
      en: 'The best-fitting route for your profile, why it was chosen, what alternatives remain, and the next step.'
    },
    'landing.step4Title': { es: 'Ejecutas tu plan', pt: 'Você executa seu plano', en: 'You execute your plan' },
    'landing.step4Body': {
      es: 'La ruta se convierte en pasos con dependencias reales: sabes qué puedes hacer hoy y qué está bloqueado hasta terminar lo anterior.',
      pt: 'A rota vira passos com dependências reais: você sabe o que pode fazer hoje e o que está bloqueado até concluir o anterior.',
      en: 'The route becomes steps with real dependencies: you know what you can do today and what stays locked until you finish the previous one.'
    },
    'landing.whatTitle': { es: 'Lo que te llevas', pt: 'O que você leva', en: 'What you take away' },
    'landing.whatSub': {
      es: 'La diferencia entre saber a dónde ir y saber cómo llegar.',
      pt: 'A diferença entre saber para onde ir e saber como chegar.',
      en: 'The difference between knowing where to go and knowing how to get there.'
    },
    'landing.f1Title': { es: 'Un puntaje que puedes auditar', pt: 'Uma pontuação que você pode auditar', en: 'A score you can audit' },
    'landing.f1Body': {
      es: 'El mismo perfil produce siempre el mismo resultado. Cada versión del motor queda registrada junto a tu evaluación.',
      pt: 'O mesmo perfil produz sempre o mesmo resultado. Cada versão do motor fica registrada junto à sua avaliação.',
      en: 'The same profile always produces the same result. Each engine version is recorded alongside your assessment.'
    },
    'landing.f1a': { es: 'Reglas explícitas, no una impresión del modelo', pt: 'Regras explícitas, não uma impressão do modelo', en: 'Explicit rules, not a model’s impression' },
    'landing.f1b': { es: 'Versionado de motor, políticas y catálogo', pt: 'Versionamento de motor, políticas e catálogo', en: 'Versioned engine, policies and catalog' },
    'landing.f2Title': { es: 'Pasos con dependencias reales', pt: 'Passos com dependências reais', en: 'Steps with real dependencies' },
    'landing.f2Body': {
      es: 'El backend hace cumplir el orden: un paso bloqueado no se puede marcar como hecho hasta completar de qué depende.',
      pt: 'O backend impõe a ordem: um passo bloqueado não pode ser marcado como feito até concluir do que ele depende.',
      en: 'The backend enforces the order: a blocked step can’t be marked done until its dependencies are complete.'
    },
    'landing.f2a': { es: 'Sabes exactamente qué desbloquea qué', pt: 'Você sabe exatamente o que desbloqueia o quê', en: 'You know exactly what unlocks what' },
    'landing.f2b': { es: 'Progreso persistente entre sesiones', pt: 'Progresso persistente entre sessões', en: 'Progress persists across sessions' },
    'landing.f3Title': { es: 'Tu caso, siempre ahí', pt: 'Seu caso, sempre lá', en: 'Your case, always there' },
    'landing.f3Body': {
      es: 'Evaluación, ruta aceptada y plan quedan guardados. Vuelves en un mes y está todo como lo dejaste.',
      pt: 'Avaliação, rota aceita e plano ficam salvos. Você volta em um mês e está tudo como deixou.',
      en: 'Assessment, accepted route and plan are saved. Come back in a month and everything is as you left it.'
    },
    'landing.f3a': { es: 'Nada se pierde al cerrar el navegador', pt: 'Nada se perde ao fechar o navegador', en: 'Nothing is lost when you close the browser' },
    'landing.f3b': { es: 'Historial completo de tu recorrido', pt: 'Histórico completo do seu percurso', en: 'Full history of your journey' },
    'landing.aiTitle': { es: 'Qué hace la IA aquí — y qué no', pt: 'O que a IA faz aqui — e o que não faz', en: 'What the AI does here — and what it doesn’t' },
    'landing.aiSub': { es: 'Preferimos decirlo antes de que lo preguntes.', pt: 'Preferimos dizer antes que você pergunte.', en: 'We’d rather say it before you ask.' },
    'landing.aiDoes': { es: 'Sí hace', pt: 'Faz sim', en: 'It does' },
    'landing.aiDoesnt': { es: 'No hace', pt: 'Não faz', en: 'It doesn’t' },
    'landing.aiDo1': { es: 'Entender tu perfil escrito en lenguaje natural', pt: 'Entender seu perfil escrito em linguagem natural', en: 'Understand your profile written in plain language' },
    'landing.aiDo2': { es: 'Redactar en palabras claras una decisión ya tomada', pt: 'Redigir em palavras claras uma decisão já tomada', en: 'Put an already-made decision into clear words' },
    'landing.aiDo3': { es: 'Resumir lo que entendió de tu situación', pt: 'Resumir o que entendeu da sua situação', en: 'Summarize what it understood about your situation' },
    'landing.aiNo1': { es: 'Elegir tu ruta migratoria', pt: 'Escolher sua rota migratória', en: 'Choose your migration route' },
    'landing.aiNo2': { es: 'Calcular tu puntaje ni tu nivel de ajuste', pt: 'Calcular sua pontuação nem seu nível de encaixe', en: 'Compute your score or fit level' },
    'landing.aiNo3': { es: 'Decidir si un paso está completo o bloqueado', pt: 'Decidir se um passo está completo ou bloqueado', en: 'Decide whether a step is complete or blocked' },
    'landing.disclaimerTitle': { es: 'MigPAL no es asesoría legal migratoria.', pt: 'O MigPAL não é assessoria jurídica migratória.', en: 'MigPAL is not legal immigration advice.' },
    'landing.disclaimerBody': {
      es: 'El catálogo de rutas que usamos hoy es un conjunto de referencia limitado, no un compendio legal verificado ni actualizado continuamente. Nada de lo que ves aquí reemplaza la opinión de un profesional habilitado, ni constituye un compromiso de resultado ante ninguna autoridad migratoria.',
      pt: 'O catálogo de rotas que usamos hoje é um conjunto de referência limitado, não um compêndio jurídico verificado nem atualizado continuamente. Nada do que você vê aqui substitui a opinião de um profissional habilitado, nem constitui compromisso de resultado perante nenhuma autoridade migratória.',
      en: 'The route catalog we use today is a limited reference set, not a verified or continuously updated legal compendium. Nothing you see here replaces the opinion of a licensed professional, nor constitutes any guarantee of outcome before any immigration authority.'
    },
    'landing.ctaBandTitle': { es: 'Deja de investigar en 40 pestañas', pt: 'Pare de pesquisar em 40 abas', en: 'Stop researching across 40 tabs' },
    'landing.ctaBandBody': {
      es: 'Cuéntanos tu situación una vez y llévate un plan que puedes empezar hoy.',
      pt: 'Conte sua situação uma vez e leve um plano que você pode começar hoje.',
      en: 'Tell us your situation once and take away a plan you can start today.'
    },
    'landing.footerNote': {
      es: '© 2026 MigPAL · Herramienta de orientación, no asesoría legal.',
      pt: '© 2026 MigPAL · Ferramenta de orientação, não assessoria jurídica.',
      en: '© 2026 MigPAL · Guidance tool, not legal advice.'
    },
    'landing.terms': { es: 'Términos', pt: 'Termos', en: 'Terms' },
    'landing.privacy': { es: 'Privacidad', pt: 'Privacidade', en: 'Privacy' },

    /* ------------------------------------------------------------- auth */
    'auth.loginTitle': { es: 'Bienvenido de vuelta', pt: 'Bem-vindo de volta', en: 'Welcome back' },
    'auth.loginSub': { es: 'Entra para retomar tu caso donde lo dejaste.', pt: 'Entre para retomar seu caso de onde parou.', en: 'Log in to pick up your case where you left off.' },
    'auth.username': { es: 'Usuario', pt: 'Usuário', en: 'Username' },
    'auth.usernamePh': { es: 'el usuario que elegiste al registrarte', pt: 'o usuário que você escolheu ao se cadastrar', en: 'the username you chose when signing up' },
    'auth.password': { es: 'Contraseña', pt: 'Senha', en: 'Password' },
    'auth.forgot': { es: '¿La olvidaste?', pt: 'Esqueceu?', en: 'Forgot it?' },
    'auth.loginBtn': { es: 'Iniciar sesión', pt: 'Entrar', en: 'Log in' },
    'auth.noAccount': { es: '¿Todavía no tienes cuenta?', pt: 'Ainda não tem conta?', en: 'Don’t have an account yet?' },
    'auth.createFree': { es: 'Crea una gratis', pt: 'Crie uma grátis', en: 'Create one free' },
    'auth.expired': { es: 'Tu sesión expiró por seguridad. Inicia sesión de nuevo para continuar.', pt: 'Sua sessão expirou por segurança. Entre novamente para continuar.', en: 'Your session expired for security. Log in again to continue.' },
    'auth.signupTitle': { es: 'Empieza tu evaluación', pt: 'Comece sua avaliação', en: 'Start your assessment' },
    'auth.signupSub': { es: 'Crea tu cuenta gratis. Sin tarjeta, sin compromiso.', pt: 'Crie sua conta grátis. Sem cartão, sem compromisso.', en: 'Create your free account. No card, no commitment.' },
    'auth.email': { es: 'Email', pt: 'E-mail', en: 'Email' },
    'auth.emailPh': { es: 'tu@ejemplo.com', pt: 'voce@exemplo.com', en: 'you@example.com' },
    'auth.usernameHint': { es: 'Mínimo 3 caracteres. Lo usarás para iniciar sesión.', pt: 'Mínimo 3 caracteres. Você o usará para entrar.', en: 'At least 3 characters. You’ll use it to log in.' },
    'auth.usernamePh2': { es: 'cómo quieres que te llamemos', pt: 'como você quer ser chamado', en: 'what should we call you' },
    'auth.passwordPh': { es: 'mínimo 8 caracteres', pt: 'mínimo 8 caracteres', en: 'at least 8 characters' },
    'auth.signupBtn': { es: 'Crear mi cuenta', pt: 'Criar minha conta', en: 'Create my account' },
    'auth.haveAccount': { es: '¿Ya tienes cuenta?', pt: 'Já tem conta?', en: 'Already have an account?' },
    'auth.loginLink': { es: 'Inicia sesión', pt: 'Entre', en: 'Log in' },
    'auth.repeatPassword': { es: 'Repite la contraseña', pt: 'Repita a senha', en: 'Repeat password' },
    'auth.repeatPasswordPh': { es: 'escríbela de nuevo', pt: 'escreva novamente', en: 'type it again' },

    'pw.0': { es: 'Usa al menos 8 caracteres.', pt: 'Use pelo menos 8 caracteres.', en: 'Use at least 8 characters.' },
    'pw.1': { es: 'Débil — agrega longitud o símbolos.', pt: 'Fraca — adicione tamanho ou símbolos.', en: 'Weak — add length or symbols.' },
    'pw.2': { es: 'Aceptable — puedes hacerla más fuerte.', pt: 'Aceitável — dá para deixar mais forte.', en: 'Acceptable — you can make it stronger.' },
    'pw.3': { es: 'Buena contraseña.', pt: 'Boa senha.', en: 'Good password.' },
    'pw.4': { es: 'Excelente contraseña.', pt: 'Senha excelente.', en: 'Excellent password.' },

    'auth.terms': {
      es: 'Al crear tu cuenta aceptas los {terms} y la {privacy}, y entiendes que MigPAL es una herramienta de orientación y no constituye asesoría legal migratoria.',
      pt: 'Ao criar sua conta você aceita os {terms} e a {privacy}, e entende que o MigPAL é uma ferramenta de orientação e não constitui assessoria jurídica migratória.',
      en: 'By creating your account you accept the {terms} and the {privacy}, and understand that MigPAL is a guidance tool and does not constitute legal immigration advice.'
    },
    'auth.termsLink': { es: 'términos y condiciones', pt: 'termos e condições', en: 'terms of service' },
    'auth.privacyLink': { es: 'política de privacidad', pt: 'política de privacidade', en: 'privacy policy' },

    /* -------------------------------------------- verificar / recuperar */
    'verify.loadingTitle': { es: 'Verificando tu cuenta…', pt: 'Verificando sua conta…', en: 'Verifying your account…' },
    'verify.loadingSub': { es: 'Un segundo.', pt: 'Um segundo.', en: 'One moment.' },
    'verify.okTitle': { es: '¡Cuenta verificada!', pt: 'Conta verificada!', en: 'Account verified!' },
    'verify.okSub': { es: 'Ya puedes usar MigPAL con tu cuenta confirmada.', pt: 'Você já pode usar o MigPAL com sua conta confirmada.', en: 'You can now use MigPAL with a confirmed account.' },
    'verify.failTitle': { es: 'No pudimos verificar', pt: 'Não conseguimos verificar', en: 'We couldn’t verify' },
    'verify.resendLabel': { es: 'Reenviar el enlace a tu email', pt: 'Reenviar o link para seu e-mail', en: 'Resend the link to your email' },
    'verify.resendBtn': { es: 'Enviarme un enlace nuevo', pt: 'Enviar um link novo', en: 'Send me a new link' },
    'verify.backLogin': { es: 'Volver a iniciar sesión', pt: 'Voltar a entrar', en: 'Back to log in' },
    'verify.noToken': { es: 'El enlace no incluye un token. Revisa que lo hayas copiado completo desde el email.', pt: 'O link не inclui um token. Verifique se você copiou o link completo do e-mail.', en: 'The link has no token. Check that you copied it fully from the email.' },
    'verify.asideQuote': { es: 'Verificar tu email protege tu cuenta.', pt: 'Verificar seu e-mail protege sua conta.', en: 'Verifying your email protects your account.' },
    'verify.aside1': { es: 'Confirma que la dirección es tuya', pt: 'Confirma que o endereço é seu', en: 'Confirms the address is yours' },
    'verify.aside2': { es: 'Te permite recuperar el acceso si olvidas la contraseña', pt: 'Permite recuperar o acesso se esquecer a senha', en: 'Lets you recover access if you forget your password' },
    'verify.aside3': { es: 'Evita que alguien registre una cuenta con tu email', pt: 'Evita que alguém registre uma conta com seu e-mail', en: 'Prevents someone registering an account with your email' },

    'forgot.title': { es: 'Recuperar tu contraseña', pt: 'Recuperar sua senha', en: 'Recover your password' },
    'forgot.sub': { es: 'Escribe tu email y te enviamos un enlace para crear una contraseña nueva.', pt: 'Escreva seu e-mail e enviaremos um link para criar uma nova senha.', en: 'Enter your email and we’ll send you a link to create a new password.' },
    'forgot.label': { es: 'Email de tu cuenta', pt: 'E-mail da sua conta', en: 'Your account email' },
    'forgot.btn': { es: 'Enviarme el enlace', pt: 'Enviar o link', en: 'Send me the link' },
    'forgot.sentTitle': { es: 'Revisa tu correo', pt: 'Verifique seu e-mail', en: 'Check your inbox' },
    'forgot.sentHint': { es: 'El enlace vence en 1 hora y solo se puede usar una vez. Si no lo ves, mira en spam.', pt: 'O link expira em 1 hora e só pode ser usado uma vez. Se não aparecer, veja no spam.', en: 'The link expires in 1 hour and can be used only once. If you don’t see it, check spam.' },
    'forgot.backLogin': { es: '← Volver a iniciar sesión', pt: '← Voltar a entrar', en: '← Back to log in' },
    'forgot.asideQuote': { es: 'Tu caso no se pierde.', pt: 'Seu caso não se perde.', en: 'Your case isn’t lost.' },
    'forgot.aside1': { es: 'Tu evaluación, tu ruta y tu plan siguen guardados', pt: 'Sua avaliação, sua rota e seu plano continuam salvos', en: 'Your assessment, route and plan stay saved' },
    'forgot.aside2': { es: 'Recuperas el acceso sin perder nada de tu progreso', pt: 'Você recupera o acesso sem perder nada do seu progresso', en: 'You regain access without losing any progress' },
    'forgot.aside3': { es: 'El enlace vence en 1 hora, por seguridad', pt: 'O link expira em 1 hora, por segurança', en: 'The link expires in 1 hour, for security' },

    'reset.title': { es: 'Crea tu contraseña nueva', pt: 'Crie sua nova senha', en: 'Create your new password' },
    'reset.sub': { es: 'Elige una contraseña que no uses en otro sitio.', pt: 'Escolha uma senha que você não use em outro site.', en: 'Pick a password you don’t use anywhere else.' },
    'reset.newPassword': { es: 'Contraseña nueva', pt: 'Nova senha', en: 'New password' },
    'reset.btn': { es: 'Guardar contraseña', pt: 'Salvar senha', en: 'Save password' },
    'reset.doneTitle': { es: 'Contraseña actualizada', pt: 'Senha atualizada', en: 'Password updated' },
    'reset.doneSub': { es: 'Ya puedes entrar con tu contraseña nueva.', pt: 'Você já pode entrar com sua nova senha.', en: 'You can now log in with your new password.' },
    'reset.invalidTitle': { es: 'Enlace no válido', pt: 'Link inválido', en: 'Invalid link' },
    'reset.invalidSub': { es: 'El enlace venció o ya se usó. Pide uno nuevo.', pt: 'O link expirou ou já foi usado. Peça um novo.', en: 'The link expired or was already used. Request a new one.' },
    'reset.requestNew': { es: 'Pedir un enlace nuevo', pt: 'Pedir um link novo', en: 'Request a new link' },
    'reset.noToken': { es: 'El enlace no incluye un token. Revisa que lo hayas copiado completo desde el email.', pt: 'O link não inclui um token. Verifique se copiou o link completo do e-mail.', en: 'The link has no token. Check that you copied it fully from the email.' },
    'reset.mismatch': { es: 'Las dos contraseñas no coinciden.', pt: 'As duas senhas não coincidem.', en: 'The two passwords don’t match.' },
    'reset.tooShort': { es: 'La contraseña necesita al menos 8 caracteres.', pt: 'A senha precisa de pelo menos 8 caracteres.', en: 'The password needs at least 8 characters.' },
    'reset.asideQuote': { es: 'Una contraseña nueva, y sigues donde estabas.', pt: 'Uma senha nova, e você continua de onde parou.', en: 'A new password, and you’re right back where you were.' },
    'reset.aside1': { es: 'Tu caso y tu progreso quedan intactos', pt: 'Seu caso e seu progresso ficam intactos', en: 'Your case and progress stay intact' },
    'reset.aside2': { es: 'El enlace solo funciona una vez', pt: 'O link só funciona uma vez', en: 'The link works only once' },
    'reset.aside3': { es: 'Tu contraseña se guarda cifrada, nunca en texto plano', pt: 'Sua senha é armazenada criptografada, nunca em texto puro', en: 'Your password is stored hashed, never in plain text' },

    /* -------------------------------------------------------- app: caso */
    'case.greeting': { es: 'Hola, {name}', pt: 'Olá, {name}', en: 'Hi, {name}' },
    'case.yourCase': { es: 'Tu caso', pt: 'Seu caso', en: 'Your case' },
    'case.refresh': { es: '↻ Actualizar', pt: '↻ Atualizar', en: '↻ Refresh' },
    'case.loadingState': { es: 'Cargando el estado de tu caso…', pt: 'Carregando o estado do seu caso…', en: 'Loading your case…' },
    'case.j1': { es: 'Perfil', pt: 'Perfil', en: 'Profile' },
    'case.j2': { es: 'Evaluación', pt: 'Avaliação', en: 'Assessment' },
    'case.j3': { es: 'Ruta', pt: 'Rota', en: 'Route' },
    'case.j4': { es: 'Mi plan', pt: 'Meu plano', en: 'My plan' },
    'case.pending': { es: 'Pendiente', pt: 'Pendente', en: 'Pending' },
    'case.ready': { es: 'Listo', pt: 'Pronto', en: 'Done' },
    'case.accepted': { es: 'Aceptada', pt: 'Aceita', en: 'Accepted' },
    'case.issued': { es: 'Emitida', pt: 'Emitida', en: 'Issued' },
    'case.discarded': { es: 'Descartada', pt: 'Descartada', en: 'Discarded' },
    'case.stepsShort': { es: '{done}/{total} pasos', pt: '{done}/{total} passos', en: '{done}/{total} steps' },

    'case.s1Title': { es: 'Cuenta tu situación', pt: 'Conte sua situação', en: 'Tell us your situation' },
    'case.s1Sub': { es: 'Escribe tu perfil o conversa con MigPAL para ordenarlo.', pt: 'Escreva seu perfil ou converse com o MigPAL para organizá-lo.', en: 'Write your profile, or chat with MigPAL to shape it.' },
    'case.profileLabel': { es: 'Tu perfil migratorio', pt: 'Seu perfil migratório', en: 'Your migration profile' },
    'case.profilePh': {
      es: 'Ej: Soy ingeniero de software con 6 años de experiencia, tengo una maestría, quiero migrar a Estados Unidos con mi pareja y tenemos algo de ahorro.',
      pt: 'Ex: Sou engenheiro de software com 6 anos de experiência, tenho mestrado, quero migrar para os Estados Unidos com meu parceiro e temos alguma poupança.',
      en: 'E.g. I’m a software engineer with 6 years of experience, I have a master’s degree, I want to move to the United States with my partner, and we have some savings.'
    },
    'case.profileHint': {
      es: 'Cuanto más concreto seas (años de experiencia, estudios, destino, familia, ahorros), mejor será tu evaluación.',
      pt: 'Quanto mais concreto você for (anos de experiência, estudos, destino, família, poupança), melhor será sua avaliação.',
      en: 'The more specific you are (years of experience, education, destination, family, savings), the better your assessment.'
    },
    'case.assessBtn': { es: 'Generar mi evaluación', pt: 'Gerar minha avaliação', en: 'Generate my assessment' },
    'case.chatToggle': { es: '💬 Prefiero conversarlo', pt: '💬 Prefiro conversar', en: '💬 I’d rather talk it through' },
    'case.chatIntro': {
      es: 'Cuéntame tu situación: a qué te dedicas, qué estudiaste, a dónde quieres migrar y con quién.',
      pt: 'Conte sua situação: com o que você trabalha, o que estudou, para onde quer migrar e com quem.',
      en: 'Tell me your situation: what you do, what you studied, where you want to move, and with whom.'
    },
    'case.chatPh': { es: 'Escribe tu mensaje…', pt: 'Escreva sua mensagem…', en: 'Type your message…' },
    'case.send': { es: 'Enviar', pt: 'Enviar', en: 'Send' },
    'case.thinking': { es: 'MigPAL está pensando…', pt: 'O MigPAL está pensando…', en: 'MigPAL is thinking…' },

    'case.s2Title': { es: 'Tu evaluación', pt: 'Sua avaliação', en: 'Your assessment' },
    'case.s2Sub': { es: 'Puntaje calculado con reglas explícitas y versionadas.', pt: 'Pontuação calculada com regras explícitas e versionadas.', en: 'Score computed with explicit, versioned rules.' },
    'case.s2EmptyTitle': { es: 'Todavía no generas tu evaluación', pt: 'Você ainda não gerou sua avaliação', en: 'You haven’t generated your assessment yet' },
    'case.s2EmptyBody': { es: 'Completa tu perfil arriba y genérala para continuar.', pt: 'Complete seu perfil acima e gere-a para continuar.', en: 'Fill in your profile above and generate it to continue.' },
    'case.confidence': { es: 'Confianza {n}%', pt: 'Confiança {n}%', en: 'Confidence {n}%' },
    'case.understood': { es: 'MigPAL entendió', pt: 'O MigPAL entendeu', en: 'MigPAL understood' },
    'case.findings': { es: 'Hallazgos', pt: 'Achados', en: 'Findings' },
    'case.recommendations': { es: 'Recomendaciones', pt: 'Recomendações', en: 'Recommendations' },
    'case.seeRoute': { es: 'Ver mi ruta recomendada', pt: 'Ver minha rota recomendada', en: 'See my recommended route' },
    'case.regenRoute': { es: 'Regenerar mi ruta', pt: 'Gerar minha rota novamente', en: 'Regenerate my route' },

    'case.s3Title': { es: 'Tu ruta recomendada', pt: 'Sua rota recomendada', en: 'Your recommended route' },
    'case.s3Sub': { es: 'La alternativa con mejor ajuste a tu perfil, y por qué.', pt: 'A alternativa com melhor encaixe no seu perfil, e por quê.', en: 'The best-fitting option for your profile, and why.' },
    'case.s3EmptyTitle': { es: 'Todavía no tienes una ruta recomendada', pt: 'Você ainda não tem uma rota recomendada', en: 'You don’t have a recommended route yet' },
    'case.s3EmptyBody': { es: 'Necesitas una evaluación primero.', pt: 'Você precisa de uma avaliação primeiro.', en: 'You need an assessment first.' },
    'case.disclaimerTitle': { es: 'Orientativo, no asesoría legal.', pt: 'Orientativo, não assessoria jurídica.', en: 'Guidance, not legal advice.' },
    'case.disclaimerBody': {
      es: 'Se calcula sobre un catálogo de referencia limitado, no sobre normativa verificada y actualizada. No reemplaza a un profesional habilitado.',
      pt: 'É calculado sobre um catálogo de referência limitado, não sobre normas verificadas e atualizadas. Não substitui um profissional habilitado.',
      en: 'It’s computed from a limited reference catalog, not from verified, up-to-date regulations. It doesn’t replace a licensed professional.'
    },
    'case.fit': { es: 'Ajuste {fit}/100 · Confianza {conf}%', pt: 'Encaixe {fit}/100 · Confiança {conf}%', en: 'Fit {fit}/100 · Confidence {conf}%' },
    'case.whyRoute': { es: 'Por qué esta ruta', pt: 'Por que esta rota', en: 'Why this route' },
    'case.docsNeeded': { es: 'Documentación que vas a necesitar', pt: 'Documentação que você vai precisar', en: 'Documents you’ll need' },
    'case.nextStep': { es: 'Próximo paso', pt: 'Próximo passo', en: 'Next step' },
    'case.alternatives': { es: 'Alternativas consideradas', pt: 'Alternativas consideradas', en: 'Alternatives considered' },
    'case.acceptRoute': { es: 'Aceptar esta ruta', pt: 'Aceitar esta rota', en: 'Accept this route' },
    'case.discardRoute': { es: 'Descartar', pt: 'Descartar', en: 'Discard' },
    'case.chooseRoute': { es: 'Elegir esta ruta', pt: 'Escolher esta rota', en: 'Choose this route' },
    'case.missingFor': { es: 'Para subir el ajuste de esta ruta, te falta: {signals}', pt: 'Para melhorar o encaixe nesta rota, falta: {signals}', en: 'To improve your fit for this route, you’re missing: {signals}' },
    'case.routeChosen': { es: 'Elegiste esta ruta — revísala arriba.', pt: 'Você escolheu esta rota — revise acima.', en: 'You chose this route — review it above.' },
    'case.signal.experience': { es: 'experiencia laboral', pt: 'experiência profissional', en: 'work experience' },
    'case.signal.education': { es: 'estudios/título', pt: 'estudos/formação', en: 'education/degree' },
    'case.signal.destination': { es: 'destino declarado', pt: 'destino declarado', en: 'stated destination' },
    'case.signal.family': { es: 'situación familiar', pt: 'situação familiar', en: 'family situation' },
    'case.signal.financial': { es: 'situación financiera', pt: 'situação financeira', en: 'financial situation' },
    'case.sourceVerified': { es: 'Requisitos según {source}, verificados el {date}.', pt: 'Requisitos segundo {source}, verificados em {date}.', en: 'Requirements per {source}, verified on {date}.' },
    'case.sourceUnverified': { es: 'Estos requisitos no pudieron verificarse contra {source}. Trátalos como orientativos y confírmalos en la fuente.', pt: 'Estes requisitos não puderam ser verificados junto a {source}. Trate-os como orientativos e confirme na fonte.', en: 'These requirements could not be verified against {source}. Treat them as guidance and confirm at the source.' },

    'case.s4Title': { es: 'Mi plan', pt: 'Meu plano', en: 'My plan' },
    'case.s4Sub': { es: 'Los pasos concretos para avanzar, en orden.', pt: 'Os passos concretos para avançar, em ordem.', en: 'The concrete steps to move forward, in order.' },
    'case.s4EmptyTitle': { es: 'Todavía no generas tu plan', pt: 'Você ainda não gerou seu plano', en: 'You haven’t generated your plan yet' },
    'case.s4EmptyBody': { es: 'Acepta una ruta recomendada para poder armarlo.', pt: 'Aceite uma rota recomendada para poder montá-lo.', en: 'Accept a recommended route to build it.' },
    'case.createPlan': { es: 'Generar mi plan de pasos', pt: 'Gerar meu plano de passos', en: 'Generate my step plan' },
    'case.seePlan': { es: 'Ver mi plan', pt: 'Ver meu plano', en: 'See my plan' },
    'case.progress': { es: '{done} de {total} pasos completados', pt: '{done} de {total} passos concluídos', en: '{done} of {total} steps completed' },
    'case.inProgress': { es: 'En curso', pt: 'Em andamento', en: 'In progress' },
    'case.completed': { es: 'Completado', pt: 'Concluído', en: 'Completed' },
    'case.blockedUntil': { es: 'Bloqueado hasta completar: {steps}', pt: 'Bloqueado até concluir: {steps}', en: 'Blocked until you complete: {steps}' },
    'case.markDone': { es: 'Marcar como completado', pt: 'Marcar como concluído', en: 'Mark as complete' },
    'case.planDoneTitle': { es: 'Completaste tu plan.', pt: 'Você concluiu seu plano.', en: 'You completed your plan.' },
    'case.planDoneBody': { es: 'Tu proyecto migratorio llegó al final de esta etapa.', pt: 'Seu projeto migratório chegou ao fim desta etapa.', en: 'Your migration project has reached the end of this stage.' },

    /* ------------------------------------------- estados y notificaciones */
    'case.subEmpty': { es: 'Empieza contándonos tu situación.', pt: 'Comece contando sua situação.', en: 'Start by telling us your situation.' },
    'case.subAssessed': { es: 'Tu evaluación está lista. Pide tu ruta recomendada.', pt: 'Sua avaliação está pronta. Peça sua rota recomendada.', en: 'Your assessment is ready. Request your recommended route.' },
    'case.subIssued': { es: 'Revisa tu ruta y acéptala para armar el plan.', pt: 'Revise sua rota e aceite-a para montar o plano.', en: 'Review your route and accept it to build the plan.' },
    'case.subAcceptedNoPlan': { es: 'Ruta aceptada. Genera tu plan de pasos.', pt: 'Rota aceita. Gere seu plano de passos.', en: 'Route accepted. Generate your step plan.' },
    'case.subDone': { es: '¡Completaste tu plan! 🎉', pt: 'Você concluiu seu plano! 🎉', en: 'You completed your plan! 🎉' },
    'case.subProgress': { es: 'Vas {done} de {total} pasos.', pt: 'Você está em {done} de {total} passos.', en: 'You’re at {done} of {total} steps.' },

    'toast.welcome': { es: '¡Bienvenido! Cuéntanos tu situación para empezar.', pt: 'Bem-vindo! Conte sua situação para começar.', en: 'Welcome! Tell us your situation to get started.' },
    'toast.assessReady': { es: 'Evaluación lista.', pt: 'Avaliação pronta.', en: 'Assessment ready.' },
    'toast.routeReady': { es: 'Ruta recomendada lista.', pt: 'Rota recomendada pronta.', en: 'Recommended route ready.' },
    'toast.routeAccepted': { es: 'Ruta aceptada. Ya puedes generar tu plan.', pt: 'Rota aceita. Você já pode gerar seu plano.', en: 'Route accepted. You can generate your plan now.' },
    'toast.routeDiscarded': { es: 'Ruta descartada.', pt: 'Rota descartada.', en: 'Route discarded.' },
    'toast.planReady': { es: 'Tu plan está listo.', pt: 'Seu plano está pronto.', en: 'Your plan is ready.' },
    'toast.planDone': { es: '¡Completaste todo tu plan! 🎉', pt: 'Você concluiu todo o seu plano! 🎉', en: 'You completed your whole plan! 🎉' },
    'toast.caseRefreshed': { es: 'Caso actualizado.', pt: 'Caso atualizado.', en: 'Case refreshed.' },
    'toast.accountCreated': { es: 'Cuenta creada. Ya puedes iniciar sesión.', pt: 'Conta criada. Você já pode entrar.', en: 'Account created. You can log in now.' },
    'toast.badCredentials': { es: 'Usuario o contraseña incorrectos.', pt: 'Usuário ou senha incorretos.', en: 'Wrong username or password.' },
    'toast.fillFields': { es: 'Completa todos los campos.', pt: 'Preencha todos os campos.', en: 'Fill in all fields.' },
    'toast.fillLogin': { es: 'Completa usuario y contraseña.', pt: 'Preencha usuário e senha.', en: 'Fill in username and password.' },
    'toast.usernameShort': { es: 'El usuario necesita al menos 3 caracteres.', pt: 'O usuário precisa de pelo menos 3 caracteres.', en: 'The username needs at least 3 characters.' },
    'toast.passwordShort': { es: 'La contraseña necesita al menos 8 caracteres.', pt: 'A senha precisa de pelo menos 8 caracteres.', en: 'The password needs at least 8 characters.' },
    'toast.profileShort': { es: 'Cuéntanos un poco más sobre tu situación (al menos 20 caracteres).', pt: 'Conte um pouco mais sobre sua situação (pelo menos 20 caracteres).', en: 'Tell us a bit more about your situation (at least 20 characters).' },
    'toast.writeEmail': { es: 'Escribe tu email.', pt: 'Escreva seu e-mail.', en: 'Enter your email.' },
    'toast.genericError': { es: 'Algo salió mal. Intenta de nuevo.', pt: 'Algo deu errado. Tente novamente.', en: 'Something went wrong. Try again.' },
    'toast.noNetwork': { es: 'No se pudo contactar al servidor. Verifica tu conexión.', pt: 'Não foi possível contatar o servidor. Verifique sua conexão.', en: 'Couldn’t reach the server. Check your connection.' },
    'toast.sessionExpired': { es: 'Tu sesión expiró. Inicia sesión de nuevo.', pt: 'Sua sessão expirou. Entre novamente.', en: 'Your session expired. Log in again.' },

    'busy.entering': { es: 'Entrando…', pt: 'Entrando…', en: 'Logging in…' },
    'busy.creating': { es: 'Creando tu cuenta…', pt: 'Criando sua conta…', en: 'Creating your account…' },
    'busy.analyzing': { es: 'Analizando tu perfil…', pt: 'Analisando seu perfil…', en: 'Analyzing your profile…' },
    'busy.findingRoute': { es: 'Buscando tu mejor ruta…', pt: 'Buscando sua melhor rota…', en: 'Finding your best route…' },
    'busy.accepting': { es: 'Aceptando…', pt: 'Aceitando…', en: 'Accepting…' },
    'busy.discarding': { es: 'Descartando…', pt: 'Descartando…', en: 'Discarding…' },
    'busy.buildingPlan': { es: 'Armando tu plan…', pt: 'Montando seu plano…', en: 'Building your plan…' },
    'busy.sending': { es: 'Enviando…', pt: 'Enviando…', en: 'Sending…' },
    'busy.saving': { es: 'Guardando…', pt: 'Salvando…', en: 'Saving…' },

    /* ------------------------------------------------------------ legal */
    'legal.draftTitle': { es: 'Borrador pendiente de revisión legal.', pt: 'Rascunho pendente de revisão jurídica.', en: 'Draft pending legal review.' },
    'legal.draftBody': {
      es: 'Este texto se redactó para reflejar con precisión cómo funciona MigPAL hoy, pero todavía no lo revisó un profesional habilitado y contiene marcadores entre corchetes que hay que completar.',
      pt: 'Este texto foi redigido para refletir com precisão como o MigPAL funciona hoje, mas ainda não foi revisado por um profissional habilitado e contém marcadores entre colchetes a completar.',
      en: 'This text was written to accurately reflect how MigPAL works today, but it has not yet been reviewed by a licensed professional and contains bracketed placeholders still to be completed.'
    },
    'legal.updated': { es: 'Última actualización: 5 de septiembre de 2026', pt: 'Última atualização: 5 de setembro de 2026', en: 'Last updated: September 5, 2026' }
  };

  function detect() {
    var saved;
    try { saved = localStorage.getItem(LANG_KEY); } catch (e) { saved = null; }
    if (saved && SUPPORTED.indexOf(saved) !== -1) return saved;

    var nav = (navigator.language || 'es').slice(0, 2).toLowerCase();
    return SUPPORTED.indexOf(nav) !== -1 ? nav : 'es';
  }

  var current = detect();

  /** Traduce una clave. `vars` reemplaza {marcadores}. Si falta la clave,
      devuelve la clave misma -- así una traducción olvidada se ve en
      pantalla en vez de romper la página con `undefined`. */
  function t(key, vars) {
    var entry = DICT[key];
    var text = entry ? (entry[current] || entry.es || key) : key;
    if (vars) {
      Object.keys(vars).forEach(function (k) {
        text = text.split('{' + k + '}').join(vars[k]);
      });
    }
    return text;
  }

  /** Aplica las traducciones al DOM. Se llama al cargar y al cambiar idioma. */
  function apply(root) {
    root = root || document;
    root.querySelectorAll('[data-i18n]').forEach(function (el) {
      el.textContent = t(el.getAttribute('data-i18n'));
    });
    root.querySelectorAll('[data-i18n-html]').forEach(function (el) {
      el.innerHTML = t(el.getAttribute('data-i18n-html'));
    });
    root.querySelectorAll('[data-i18n-placeholder]').forEach(function (el) {
      el.placeholder = t(el.getAttribute('data-i18n-placeholder'));
    });
    root.querySelectorAll('[data-i18n-title]').forEach(function (el) {
      el.title = t(el.getAttribute('data-i18n-title'));
    });
    root.querySelectorAll('[data-i18n-aria]').forEach(function (el) {
      el.setAttribute('aria-label', t(el.getAttribute('data-i18n-aria')));
    });
    document.documentElement.lang = current;
  }

  function set(lang) {
    if (SUPPORTED.indexOf(lang) === -1) return;
    current = lang;
    try { localStorage.setItem(LANG_KEY, lang); } catch (e) { /* noop */ }
    apply();
    document.dispatchEvent(new CustomEvent('migpal:langchange', { detail: { lang: lang } }));
  }

  /** Selector de idioma para el header. Se construye en JS para no repetir
      el mismo bloque de markup en las 8 páginas. */
  function mountSelector(container) {
    if (!container) return;
    var names = { es: 'ES', pt: 'PT', en: 'EN' };
    var select = document.createElement('select');
    select.className = 'lang-select';
    select.setAttribute('aria-label', t('common.language'));
    SUPPORTED.forEach(function (lang) {
      var opt = document.createElement('option');
      opt.value = lang;
      opt.textContent = names[lang];
      if (lang === current) opt.selected = true;
      select.appendChild(opt);
    });
    select.addEventListener('change', function () { set(select.value); });
    container.insertBefore(select, container.firstChild);
  }

  document.addEventListener('DOMContentLoaded', function () {
    apply();
    mountSelector(document.querySelector('.header-actions'));
  });

  return { t: t, set: set, apply: apply, get lang() { return current; }, supported: SUPPORTED };
})();
